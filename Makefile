.PHONY: build rm intoto-test

rm:
	docker-compose down
	docker-compose rm --force -v
	docker volume rm master_psql

build:
	docker-compose up

intoto-test:
	(cd test; python create_tree.py --new --append 10)
	(cd test; python create_tree.py --submissions)
