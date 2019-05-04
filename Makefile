.PHONY: build
build:
	docker-compose up

rm:
	docker-compose rm --force -v
	docker volume rm master_psql
