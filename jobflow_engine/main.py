from fastapi import FastAPI

app = FastAPI(title="jobflow_engine")


@app.get("/health")
def health_check():
    return {"status": "healthy"}