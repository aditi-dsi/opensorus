from modal import Image, asgi_app, App, Secret

app = App("opensorus-server")

image = Image.debian_slim().pip_install(
    "fastapi",
    "uvicorn",
    "cryptography==45.0.3",
    "gradio==5.33.0",
    "llama_index==0.12.40",
    "llama_index.llms.mistralai",
    "llama_index.embeddings.mistralai",
    "mistralai==1.8.1",
    "PyJWT==2.10.1",
    "python-dotenv==1.1.0",
    "scikit-learn==1.6.1",
    "requests==2.32.3"
)

image = image.add_local_python_source("server")
image = image.add_local_python_source("agent")
image = image.add_local_python_source("tools")
image = image.add_local_python_source("config")


@app.function(image=image, secrets=[Secret.from_name("SECRET")])
@asgi_app()
def fastapi_app():
    import sys
    sys.path.append("/root")
    from server.main import app
    return app

if __name__ == "__main__":
    app.serve()