proj=pyproject.toml

# Get version; kind of klugdy, but works.
version=$(grep -Po  "version = \"\K\d.\d.\d" $proj)

compiled_version=$(./job --version)

if [ $version != $compiled_version ]; then
  echo "Compiled version ($compiled_version) does not match project version ($version)."
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "There are uncommited changes." 
  exit 1
fi

if [ -n "$(git log '@{u}..HEAD')" ]; then
  echo "There are local commits not pushed to remote."
  exit 1
fi 

gh release create "$version" job --title "$version" --notes "See CHANGELOG.md" 