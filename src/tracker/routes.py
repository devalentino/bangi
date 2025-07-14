from robyn import SubRouter

router = SubRouter(__file__)


@router.post("/health")
async def add_crime():
    return 'Hello, World!'