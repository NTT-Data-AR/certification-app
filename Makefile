validate:
	python scripts/validate_repository.py

tree:
	find . -maxdepth 4 -type f | sort
