IMAGE=paint-content-pro

build:
	docker build -t $(IMAGE) .

run: build
	docker run -it --rm \
		-v $(PWD)/agent:/app \
		-p 5000:5000 \
		--env-file agent/.env \
		$(IMAGE)

draft: build
	@read -p "Community: " community; \
	docker run -it --rm \
		-v $(PWD)/agent:/app \
		--env-file agent/.env \
		$(IMAGE) python agent.py draft --community "$$community"

status: build
	docker run -it --rm \
		-v $(PWD)/agent:/app \
		--env-file agent/.env \
		$(IMAGE) python agent.py status
