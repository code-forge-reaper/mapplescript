echo "--- checking mapple---"
for file in $(command -p ls mapple/*.py); do
	echo "linting $file"
	pylint $file
done
echo "--- checking stdlib ---"
for file in $(command -p ls modules/*.py); do
	echo "linting $file"
	pylint --init-hook="import sys; sys.path.append('.')" $file
done
