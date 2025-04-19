from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from src.ai_advisor.tools.course_catalog_tool import CourseCatalogTool
from src.ai_advisor.tools.degree_program_url_tool import DegreeProgramUrlTool

# Advanced configuration with detailed parameters
llm = LLM(
    model="openai/gpt-4o-mini",
    temperature=0.8,        # Higher for more creative outputs
    timeout=120,           # Seconds to wait for response
    max_tokens=4000,       # Maximum length of response
    top_p=0.9,            # Nucleus sampling parameter
    frequency_penalty=0.1, # Reduce repetition
    presence_penalty=0.1,  # Encourage topic diversity
    # response_format={"type": "json"},  # For structured outputs
    seed=42               # For reproducible results
)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class AiAdvisor():
    """AiAdvisor crew for course recommendations"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    # @agent
    # def course_advisor(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['course_advisor'],
    #         verbose=True
    #     )

    @agent
    def catalog_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['catalog_specialist'],
            tools=[CourseCatalogTool(), DegreeProgramUrlTool()],
            verbose=True,
            llm=llm
        )

    @task
    def recommend_courses(self) -> Task:
        return Task(
            config=self.tasks_config['recommend_courses'],
            output_file='course_recommendations.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AiAdvisor crew for course recommendations"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
