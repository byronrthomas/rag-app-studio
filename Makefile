.PHONY: build-fe-builder

build-fe-builder:
	cd frontend;\
	fnm use;\
	npm run build:builder;\
	cd ..;\
	rm -rf rag_studio/builder_static;\
	cp -R frontend/apps/builder/dist ./rag_studio/builder_static;
