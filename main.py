from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

from database.metric import get_metrics
from database.postgres_sql import create_database
from database.create_table import create_tables

from fastapi.encoders import jsonable_encoder
from app.routes.ingestion import router as ingestion_router
from app.routes.chat import router as chat_router

load_dotenv()

app = FastAPI(
    title="AI-Powered Investor Intelligence Platform"
)


@app.on_event("startup")
def startup_event():
    """
    Initialize database and vector index on app startup.
    """
    create_database()
    create_tables()
    # We do not call create_index() here because QdrantStoreManager 
    # automatically creates the index if it does not exist during document upload.
    # Additionally, vectorstore/create_index.py wipes the database unconditionally!
    print("Startup sequence complete.")

app.include_router(
    ingestion_router,
    prefix="/api",
    tags=["Ingestion"]
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"]
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)


@app.get("/")
def dashboard(request: Request):
    """
    Render dashboard UI.
    """
    metrics = jsonable_encoder(get_metrics())

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "metrics": metrics,
            "total_companies": len(metrics),
            "total_reports": len(metrics)
        }
    )


@app.get("/api/metrics")
def metrics():
    """
    Return KPI metrics.
    """
    return JSONResponse(
        content=jsonable_encoder(get_metrics())
    )


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )




# from fastapi import FastAPI, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# import uvicorn

# from app.routes.dashboard import router as dashboard_router, get_metrics
# from app.routes.health import router as health_router
# from app.routes.chat import router as chat_router
# from app.routes.ingestion import router as ingestion_router

# app = FastAPI(
#     title="Investor Intelligence API",
#     version="1.0.0"
# )

# app.mount("/static", StaticFiles(directory="app/static"), name="static")
# templates = Jinja2Templates(directory="app/templates")

# @app.get("/")
# def render_dashboard(request: Request):
#     metrics = get_metrics()
    
#     total_companies = len(set(row.get("company") for row in metrics if row.get("company"))) if metrics else 0
#     total_reports = len(metrics) if metrics else 0
    
#     return templates.TemplateResponse(
#         request=request,
#         name="dashboard.html",
#         context={
#             "metrics": metrics,
#             "total_companies": total_companies,
#             "total_reports": total_reports
#         }
#     )

# app.include_router(
#     health_router,
#     tags=["Health"]
# )

# app.include_router(
#     dashboard_router,
#     prefix="/api",
#     tags=["Dashboard"]
# )

# app.include_router(
#     chat_router,
#     prefix="/api",
#     tags=["Chat"]
# )

# app.include_router(
#     ingestion_router,
#     prefix="/api",
#     tags=["Ingestion"]
# )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8080)
