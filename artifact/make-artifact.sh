#!/bin/sh
# Builds the artifact archive to be uploaded to Zenodo.
# Requires git, docker, zip and network access (only while building).
# The image is x86-64; on Apple Silicon it is built and tested under emulation.
# Usage, from anywhere: artifact/make-artifact.sh [output_dir]
# Produces <output_dir>/maqsharp-artifact.zip and its SHA256 checksum.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mkdir -p "${1:-$ROOT/dist}" && cd "${1:-$ROOT/dist}" && pwd)"
NAME=maqsharp-artifact
TAG=maqsharp:spin27
cd "$ROOT"

if [ -n "$(git status --porcelain --ignore-submodules=none)" ]; then
  echo "The working tree has uncommitted changes; commit them first so that the"
  echo "sources in the archive and in the image are the same."; exit 1
fi
git submodule update --init

echo "== building the Docker image $TAG"
docker build --platform linux/amd64 -f artifact/Dockerfile -t "$TAG" .

echo "== smoke test inside the image, without network"
docker run --rm --platform linux/amd64 --network none "$TAG" ../artifact/smoke-test.sh

echo "== assembling $OUT/$NAME"
rm -rf "${OUT:?}/$NAME" "$OUT/$NAME.zip" "$OUT/$NAME.zip.sha256"
mkdir -p "$OUT/$NAME"
git archive --prefix=MaQ/ HEAD | tar -x -C "$OUT/$NAME"
(cd common/as4qc && git archive --prefix=MaQ/common/as4qc/ HEAD) | tar -x -C "$OUT/$NAME"
docker save "$TAG" | gzip > "$OUT/$NAME/maqsharp-image.tar.gz"
cp artifact/README.md "$OUT/$NAME/README.md"
cp artifact/License.txt "$OUT/$NAME/License.txt"

if command -v sha256sum >/dev/null; then SHA="sha256sum"; else SHA="shasum -a 256"; fi
(cd "$OUT" && zip -qr "$NAME.zip" "$NAME" && $SHA "$NAME.zip" | tee "$NAME.zip.sha256")
echo "Upload $OUT/$NAME.zip to Zenodo and put its DOI and the checksum above in the submission."
