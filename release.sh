proj=pyproject.toml

# Get version; kind of klugdy, but works.
version=$(grep -Po  "version = \"\K\d.\d.\d" $proj)

compiled_version=$(./job --version)

if [ $version != $compiled_version ]; then
  echo "Compiled version ($compiled_version) does not match project version ($version)"
  exit 1
fi

gh release create $version job --generate-notes 