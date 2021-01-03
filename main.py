from fairy_note.factory import get_app

app = get_app()
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8889, log_level="info")
