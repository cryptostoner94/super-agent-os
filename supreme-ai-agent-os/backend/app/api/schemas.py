from pydantic import BaseModel

class AgentRequest(BaseModel):
    prompt: str = ""
    raw_data: str = ""
    file_text: str = ""
    agent_id: str = "executive"
    timeout: int = 120

class CommandRequest(BaseModel):
    command: str
    timeout: int = 120

class LibraryItem(BaseModel):
    title: str
    type: str = "Document"
    content: str = ""

class ArtifactRequest(BaseModel):
    title: str = "Untitled"
    content: str = ""
    format: str = "markdown"
