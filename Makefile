.PHONY: build-fe-builder

build-fe-builder:
	cd frontend;\
	fnm use;\
	npm run build:builder;\
	cd ..;\
	rm -rf rag_studio/builder_static;\
	cp -R frontend/apps/builder/dist ./rag_studio/builder_static;

.PHONY: build-fe-runner

build-fe-runner:
	cd frontend;\
	fnm use;\
	npm run build:runner;\
	cd ..;\
	rm -rf rag_studio/runner_static;\
	cp -R frontend/apps/runner/dist ./rag_studio/runner_static;

.PHONY: run-fe-builder

run-fe-builder:
	cd frontend;\
	fnm use;\
	npm run dev:builder;

.PHONY: run-fe-runner

run-fe-runner:
	cd frontend;\
	fnm use;\
	npm run dev:runner;