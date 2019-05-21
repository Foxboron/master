.PHONY: build rm down intoto-test transport-test

rm:
	docker-compose down
	docker-compose rm --force -v
	docker volume rm master_psql

build:
	@docker-compose up

down:
	@docker-compose down

intoto-test:
	(cd test; python create_tree.py --new --append 10)
	(cd test; python create_tree.py --submissions)


stress-data:
	(cd test; python create_tree.py --new --append 110000)

transport-test:
	@echo -e "\e[1m[*] Starting\e[0m"
	@docker-compose up -d postgres master
	@echo -e "\e[1m[*] Waiting for system to start...\e[0m"
	@while ! curl "0.0.0.0:5000/api/log/tree/stats" &> /dev/null; do sleep 3; done
	@echo -e "\e[1m[*] Adding test data...\e[0m"
	@docker-compose exec master make -C /app intoto-test
	@echo -e "\e[1m[*] Running test suite...\e[0m"
	@docker-compose up apt
	@echo -e "\e[1m[*] Removing containers...\e[0m"
	@docker-compose down
	@docker-compose rm --force -v
	@docker volume rm master_psql

stress-test:
	@echo -e "\e[1m[*] Starting\e[0m"
	@docker-compose up -d postgres master
	@echo -e "\e[1m[*] Waiting for system to start...\e[0m"
	@while ! curl "0.0.0.0:5000/api/log/tree/stats" &> /dev/null; do sleep 3; done
	@echo -e "\e[1m[*] Adding 110000 elements to the tree - THIS WILL TAKE A WHILE...\e[0m"
	@docker-compose exec master make -C /app stress-data 
	@echo -e "\e[1m[*] Copying stats.txt and roots.txt locally...\e[0m"
	@docker-compose exec master cat /app/test/stats.txt > stats.txt
	@docker-compose exec master cat /app/test/roots.txt > roots.txt
