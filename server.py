import os

import uvicorn


def main() -> None:
    port = int(os.environ.get('PORT', '5174'))
    uvicorn.run('backend.app:app', host='0.0.0.0', port=port, reload=False)


if __name__ == '__main__':
    main()
