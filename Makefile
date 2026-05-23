.PHONY: test verify verify-prefix certificate certificate-prefix article note clean

test:
	PYTHONPATH=src pytest

verify:
	PYTHONPATH=src python -m unit_distance_gs_optimiser.cli verify certificates/t81-swap-197-337-to-433-601.json

verify-prefix:
	PYTHONPATH=src python -m unit_distance_gs_optimiser.cli verify certificates/t81-first-odd-primes.json

certificate:
	PYTHONPATH=src python -m unit_distance_gs_optimiser.cli search-t --t-certificate certificates/t81-swap-197-337-to-433-601.json --prime-limit 200000 --name t81-swap-197-337-to-433-601-regenerated --write-certificate certificates/t81-swap-197-337-to-433-601-regenerated.json

certificate-prefix:
	PYTHONPATH=src python -m unit_distance_gs_optimiser.cli search --t-size 81 --prime-limit 200000 --name t81-first-odd-primes-exponent-1.031722120036 --write-certificate certificates/t81-first-odd-primes.json

article:
	cd notes && pdflatex -interaction=nonstopmode sawin_parameter_optimisation.tex && pdflatex -interaction=nonstopmode sawin_parameter_optimisation.tex

note: article

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache -o -name .ipynb_checkpoints \) -prune -exec rm -rf {} +
	rm -f notes/*.aux notes/*.bbl notes/*.blg notes/*.log notes/*.out notes/*.toc
