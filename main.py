from fastapi import FastAPI

app = FastAPI(
	title='NOC API',
	description='Network Operation Center API Platform',
	version='0.0.1'
)

@app.get('/')
async def default():
	return 'Default route'

