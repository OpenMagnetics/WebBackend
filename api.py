from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from app.backend.models import BugReportsTable, TelemetryTable
from app.backend.models import BugReport
from app.backend.mas_models import CoreShape
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import os
import kombu
import celery
import PyOpenMagnetics
from OpenMagneticsVirtualBuilder.builder import Builder as ShapeBuilder  # noqa: E402
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app/backend')))
from plotter import purge_queue
from plotter import task_generate_core_3d_model
from plotter import task_generate_core_technical_drawing, task_generate_gapping_technical_drawing
import ast
import httpx

temp_folder = "/opt/openmagnetics/temp"
high_performance_backend_url = "http://86.127.248.99:8001"
use_celery = ast.literal_eval(os.getenv('USE_CELERY', "True"))
use_db = "OM_DB_ADDRESS" in os.environ


from app.backend.accounts.routers import auth_router, designs_router, inventory_router, me_router, orgs_router, shares_router

app = FastAPI()

# uvicorn serves this API directly (no nginx in front), so the request-size
# cap lives here. 10 MB comfortably covers the largest observed MAS payloads
# (~1.5 MB) and the future ndjson inventory imports.
MAX_BODY_BYTES = 10 * 1024 * 1024


@app.middleware("http")
async def reject_oversized_bodies(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return Response(status_code=413, content="Request body too large")
    return await call_next(request)


app.include_router(auth_router)
app.include_router(designs_router)
app.include_router(inventory_router)
app.include_router(me_router)
app.include_router(orgs_router)
app.include_router(shares_router)

origins = [
    "https://openmagnetics.com",
    "https://beta.openmagnetics.com",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def read_root():
    return {"Hello": "World"}


@app.post("/report_bug", include_in_schema=False)
def report_bug(data: BugReport):
    data = data.dict()

    bug_reports_table = BugReportsTable()
    bug_report_id = bug_reports_table.report_bug(data['username'], data['userDataDump'], data['userInformation'])
    return {"status": "reported", "bug_report_id": bug_report_id}


@app.post("/core_compute_shape_stl", include_in_schema=False)
@app.post("/core_compute_shape", include_in_schema=False)
def core_compute_shape(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder("FreeCAD").factory(coreShape)
    core_builder.set_output_path(temp_folder)
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        purge_queue()
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(stl_path)


@app.post("/core_compute_shape_stp", include_in_schema=False)
def core_compute_shape_stp(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder("FreeCAD").factory(coreShape)
    core_builder.set_output_path(temp_folder)
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        purge_queue()
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(step_path)


@app.post("/core_compute_core_3d_model_stl", include_in_schema=False)
@app.post("/core_compute_core_3d_model", include_in_schema=False)
async def core_compute_core_3d_model(request: Request):
    core = await request.json()
    number_retries = 5
    stl_data = None

    if not use_celery:
        print("not use_celery")
        stl_data = task_generate_core_3d_model(core, temp_folder)
    else:
        try:
            for retry in range(number_retries):
                result = task_generate_core_3d_model.delay(core, temp_folder)
                try:
                    stl_data = result.get(timeout=10)
                except celery.exceptions.TimeoutError:
                    continue
                except ConnectionResetError:
                    continue
                if stl_data is not None:
                    break
                print("Retrying task_generate_core_3d_model")
            if stl_data is None:
                purge_queue()
        except kombu.exceptions.OperationalError:
            stl_data = task_generate_core_3d_model(core, temp_folder)

    if stl_data is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return stl_data


@app.post("/core_compute_core_3d_model_stp", include_in_schema=False)
async def core_compute_core_3d_model_stp(request: Request):
    core = await request.json()
    number_retries = 5
    stp_data = None

    if not use_celery:
        stp_data = task_generate_core_3d_model(core, temp_folder, False)
    else:
        try:
            for retry in range(number_retries):
                result = task_generate_core_3d_model.delay(core, temp_folder, False)
                try:
                    stp_data = result.get(timeout=10)
                except celery.exceptions.TimeoutError:
                    continue
                except ConnectionResetError:
                    continue
                if stp_data is not None:
                    break
                print("Retrying task_generate_core_3d_model")
            if stp_data is None:
                purge_queue()
        except kombu.exceptions.OperationalError:
            stp_data = task_generate_core_3d_model(core, temp_folder, False)

    if stp_data is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return stp_data


@app.post("/core_compute_technical_drawing", include_in_schema=False)
async def core_compute_technical_drawing(request: Request):
    data = await request.json()
    number_retries = 5
    views = None

    if not use_celery:
        views = task_generate_core_technical_drawing(data, temp_folder)
    else:
        try:
            for retry in range(number_retries):
                result = task_generate_core_technical_drawing.delay(data, temp_folder)
                try:
                    views = result.get(timeout=10)
                except celery.exceptions.TimeoutError:
                    continue
                except ConnectionResetError:
                    continue
                if views is not None:
                    break
                print("Retrying task_generate_core_technical_drawing")
            if views is None:
                purge_queue()
        except kombu.exceptions.OperationalError:
            views = task_generate_core_technical_drawing(data, temp_folder)

    if views is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return views


@app.post("/core_compute_gapping_technical_drawing", include_in_schema=False)
async def core_compute_gapping_technical_drawing(request: Request):
    data = await request.json()
    number_retries = 5
    views = None

    if not use_celery:
        views = task_generate_core_technical_drawing(data, temp_folder)
    else:
        try:
            for retry in range(number_retries):
                result = task_generate_gapping_technical_drawing.delay(data, temp_folder)
                try:
                    views = result.get(timeout=10)
                except celery.exceptions.TimeoutError:
                    continue
                except ConnectionResetError:
                    continue
                if views is not None:
                    break
                print("Retrying task_generate_gapping_technical_drawing")
            if views is None:
                purge_queue()
        except kombu.exceptions.OperationalError:
            views = task_generate_core_technical_drawing(data, temp_folder)

    if views is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return views


def insert_telemetry_background(data, environment):
    table = TelemetryTable()
    table.record(
        session_id=data.get('session_id', 'unknown'),
        event_type=data.get('event_type', ''),
        source=data.get('source', ''),
        stage=data.get('stage'),
        environment=environment,
        app_version=data.get('app_version'),
        mas_data=data.get('mas_data'),
        topology=data.get('topology'),
        mas_version=data.get('mas_version'),
        result_count=data.get('result_count'),
        error_message=data.get('error_message'),
    )


@app.post("/telemetry", include_in_schema=False)
async def telemetry(request: Request, background_tasks: BackgroundTasks):
    if use_db:
        data = await request.json()
        # The frontend build declares its environment (VITE_ENV). Trust it when
        # valid; otherwise fall back to the backend's own OM_ENV. Defaults to
        # production only as a last resort so untagged rows never masquerade as
        # development (which would hide them from production stats).
        env = data.get('environment')
        if env not in ('development', 'production'):
            env = "development" if os.getenv("OM_ENV", "production") == "development" else "production"
        background_tasks.add_task(insert_telemetry_background, data, env)
        return "Inserting in the background"
    else:
        return "DB not available"


@app.post("/load_external_core_materials", include_in_schema=False)
async def load_external_core_materials(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    external_core_materials_string = data["coreMaterialsString"]

    PyOpenMagnetics.load_core_materials(external_core_materials_string)
    PyOpenMagnetics.load_core_materials("")
    return "Data loaded"


@app.post("/create_simulation_from_mas", include_in_schema=False)
async def create_simulation_from_mas(request: Request):
    data = await request.json()
    url = f'{high_performance_backend_url}/create_simulation_from_mas'
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, timeout=600)
        return Response(content=response.content, media_type="binary/octet-stream")


@app.post("/is_high_performance_backend_available", include_in_schema=False)
async def is_high_performance_backend_available():
    try:
        url = f'{high_performance_backend_url}/remote_available'
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=5)
            print("Remote available")
            return True
    except Exception:
        return False
