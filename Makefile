api-test:
	$(MAKE) -C apps/api test

api-lint:
	$(MAKE) -C apps/api lint

api-pytest:
	$(MAKE) -C apps/api pytest

api-migrate:
	$(MAKE) -C apps/api migrate

web-install:
	npm --prefix apps/web ci

web-build:
	npm --prefix apps/web run build

web-start:
	npm --prefix apps/web run start

web-openapi-download:
	npm --prefix apps/web run openapi:download

web-openapi-check:
	npm --prefix apps/web run openapi:check
