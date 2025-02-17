from crewai_tools import BaseTool

class CustomSerperDevTool(BaseTool):
    name : str = "custom"
    description: str = "bitnews"

    def _run(self, query: str) ->str:
        """
        news
        """
        return "This is Test"