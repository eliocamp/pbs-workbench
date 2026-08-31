proj=pyproject.toml

# Get version; kind of klugdy, but works.
version=$(grep -Po  "version = \"\K\d.\d.\d" $proj)

gh release create $version job --generate-notes