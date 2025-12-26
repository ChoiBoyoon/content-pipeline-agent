from calendar import c
from typing import List
import json
import re
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai import Agent
from crewai import LLM
from pydantic import BaseModel
from tools import web_search_tool
from seo_crew import SeoCrew
from virality_crew import ViralityCrew

class BlogPost(BaseModel):
    title: str
    subtitle: str
    sections: List[str]

class Tweet(BaseModel):
    content: str
    hashtags: str

class LinkedInPost(BaseModel):
    hook: str
    content: str
    call_to_acction: str

class Score(BaseModel):
    score: int=0
    reason: str=""


class ContentPipelineState(BaseModel):
    #inputs
    content_type: str=""
    topic: str=""
    
    #internal
    max_length: int=0
    research: str=""
    score: Score | None = None

    #content
    blog_post: BlogPost | None = None
    tweet: Tweet | None = None
    linkedin_post: LinkedInPost | None = None

class ContentPipelineFlow(Flow[ContentPipelineState]):
    @start()
    def init_content_pipeline(self): #validate the state
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError("The content type is not valid.")

        if self.state.topic=="":
            raise ValueError("The topic can't be empty.")

        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type=="blog":
            self.state.max_length=800
        elif self.state.content_type=="linkedin":
            self.state.max_length=500

    @listen(init_content_pipeline)
    def conduct_research(self):
        researcher = Agent(
            role="Head Researcher",
            backstory="You're like a digital detective who loves digging up fascinating facts and insights. You have a knack for finding the good stuff that others miss.",
            goal=f"Find the most interesting and useful info about {self.state.topic}",
            tools=[web_search_tool],
            max_iter=2  # 테스트 중이므로 반복 횟수 제한
        )
        research_result = researcher.kickoff(f"Find the most interesting and useful info about {self.state.topic}. Keep the response concise and under 500 words.")
        # Research 결과를 문자열로 변환하고 길이 제한 (테스트 중 토큰 절약)
        research_str = str(research_result)
        self.state.research = research_str[:2000] if len(research_str) > 2000 else research_str

    @router(conduct_research)
    def conduct_research_router(self):
        content_type=self.state.content_type

        if content_type=="blog":
            return "make_blog"
        elif content_type=="tweet":
            return "make_tweet"
        elif content_type=="linkedin":
            return "make_linkedin_post"

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        """
        if blog post has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making blog...")
        blog_post=self.state.blog_post
        
        llm = LLM(model="openai/gpt-5-mini") # 테스트 중 토큰 절약을 위해 max_tokens 제한

        if blog_post is None:
            result = llm.call(
                f"""
                You must return a JSON object matching this exact structure:
                {{
                    "title": "string",
                    "subtitle": "string", 
                    "sections": ["string1", "string2", ...]
                }}

                Make a VERY SHORT blog post that can go viral on the topic {self.state.topic}. 
                - Maximum total length: {self.state.max_length} words
                - Keep title under 10 words
                - Keep subtitle under 15 words  
                - Each section should be 2-3 sentences maximum (50 words max per section)
                - Use only 2-3 sections total
                - Return ONLY valid JSON, no additional text before or after

                Use the following research:
                            
                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """,
                max_tokens=200,  # 테스트 중 토큰 절약
                temperature=0.3  # 더 결정적인 출력
            )
            # JSON 파싱 시도
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                self.state.blog_post = BlogPost(**json.loads(json_match.group()))
            else:
                # 파싱 실패 시 직접 파싱 시도
                self.state.blog_post = BlogPost.model_validate_json(result)
        else:
            result = llm.call(
                f"""
                You must return a JSON object matching this exact structure:
                {{
                    "title": "string",
                    "subtitle": "string", 
                    "sections": ["string1", "string2", ...]
                }}

                You wrote the following blog post on {self.state.topic}, but it does not have a good SEO score because {self.state.score.reason}. 
                Improve it while keeping it under {self.state.max_length} words total.
                - Keep title under 10 words
                - Keep subtitle under 15 words  
                - Each section should be 2-3 sentences maximum (50 words max per section)
                - Use only 2-3 sections total
                - Return ONLY valid JSON, no additional text before or after

                <blog_post>
                {self.state.blog_post.model_dump_json()}
                </blog_post>

                Use the following research:
                            
                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """,
                max_tokens=200,  # 테스트 중 토큰 절약
                temperature=0.3  # 더 결정적인 출력
            )
            # JSON 파싱 시도
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                self.state.blog_post = BlogPost(**json.loads(json_match.group()))
            else:
                self.state.blog_post = BlogPost.model_validate_json(result)

    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        """
        if tweet has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making tweet...")
        tweet = self.state.tweet
        llm = LLM(model = "openai/gpt-5-mini", response_format=Tweet)
        if tweet is None:
            result=llm.call(
                f"""
                Make a tweet that can go viral on the topic {self.state.topic} using the following research:
                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """
            )
        else:
            result=llm.call(
                f"""
                You wrote this tweet on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason}. Improve it.

                <tweet>
                ===============
                {self.state.tweet.model_dump_json()}
                ===============
                </tweet>

                Use the following research.

                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """
            )
        self.state.tweet = Tweet.model_validate_json(result) #CrewAI의 버그. 요청한 object대신 str을 줌..

    @listen(or_("make_linkedin_post", "remake_linkedin_post"))
    def handle_make_linkedin_post(self):
        """
        if linkedin post has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making linkedin post...")
        linkedin_post=self.state.linkedin_post
        llm = LLM(model="openai/gpt-5-mini", response_format=LinkedInPost)
        if linkedin_post is None:
            self.state.linkedin_post=llm.call(
                f"""
                Make a linkedin post with SEO practices on the topic {self.state.topic} using the following research:
                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """
            )
        else:
            self.state.linkedin_post=llm.call(
                f"""
                You wrote this linkedin post on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason}. Improve it.

                <linkedin_post>
                ===============
                {self.state.linkedin_post.model_dump_json()}
                ===============
                </linkedin_post>

                Use the following research.

                <research>
                ===============
                {self.state.research}
                ===============
                </research>
                """
            )

    @listen(handle_make_blog)
    def check_seo(self):
        result = SeoCrew().crew().kickoff(inputs={'topic':self.state.topic, 'blog_post':self.state.blog_post.model_dump_json()})
        self.state.score = result.pydantic

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        result = (
            ViralityCrew().crew().kickoff(inputs={
                "topic":self.state.topic, 
                "content_type":self.state.content_type,
                "content": (self.state.tweet.model_dump_json() if self.content.content_type=="tweet" else self.state.linkedin_post.model_dump_json())
                })
            self.state.score = result.pydantic
        )

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score

        print(score)

        #if the score is not high enough, remake the post
        if score.score>=8:
            return "check_passed"
        else:
            if content_type=="blog":
                return "remake_blog"
            elif content_type=="linkedin":
                return "remake_linkedin"
            else:
                return "remake_tweet"

    @listen("check_passed")
    def finalize_content(self):
        """Finalize the content"""
        print("🎉 Finalizing content...")
        if self.state.content_type == "blog":
            print(f"📝 Blog Post: {self.state.blog_post.title}")
            print(f"🔍 SEO Score: {self.state.seo_score}/100")
        elif self.state.content_type == "tweet":
            print(f"🐦 Tweet: {self.state.tweet}")
            print(f"🚀 Virality Score: {self.state.virality_score}/100")
        elif self.state.content_type == "linkedin":
            print(f"💼 LinkedIn: {self.state.linkedin_post.title}")
            print(f"🚀 Virality Score: {self.state.virality_score}/100")
        
        print("✅ Content ready for publication!")
        return (self.state.linkedin_post if self.state.content_type=="linkedin" else (self.state.tweet if self.state.content_type=="tweet" else self.state.blog_post))

flow = ContentPipelineFlow()
# flow.plot()
flow.kickoff(inputs={"content_type":"blog", "topic":"AI pharma"})
