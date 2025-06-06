from fastapi import FastAPI, HTTPException
from agent.core import run_agent

app = FastAPI()

@app.post('/webhook')
async def check_payload(payload: dict):
    if "action" in payload:
        if payload["action"] == "created":
            if payload["comment"]["body"] == "@opensorus" or payload["comment"]["body"] == "@OpenSorus":
                
                print("This issue is assigned to OpenSorus Agent.")
                issue_url = payload["issue"]["url"]
                print("URL", issue_url)
                branch_name = payload["repository"]["default_branch"]
                print("Branch Name", branch_name)
                result = await run_agent(issue_url, branch_name)
                return {"message": result or "This issue is assigned to OpenSorus Agent."}
        else:
            raise HTTPException(status_code=400, detail="Unknown action.")
    else:
        raise HTTPException(status_code=400, detail="No valid payload.")
    
@app.get('/health')
def health_check():
    return {"status": "Hello World!, I am alive!"}