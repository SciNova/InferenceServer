LLAMA_CPP_REPO := https://github.com/ggerganov/llama.cpp.git
LLAMA_CPP_DIR := build/llama.cpp
BUILD_DIR := $(LLAMA_CPP_DIR)/out
JOBS := $(shell nproc 2>/dev/null || echo 4)

.PHONY: all sources clean

all: llama-server

sources:
	if [ -d $(LLAMA_CPP_DIR)/.git ]; then \
		cd $(LLAMA_CPP_DIR) && git fetch origin && git checkout origin/HEAD; \
	else \
		git clone $(LLAMA_CPP_REPO) $(LLAMA_CPP_DIR); \
	fi

$(BUILD_DIR)/bin/llama-server: sources
	cmake -B $(BUILD_DIR) -S $(LLAMA_CPP_DIR) \
		-DCMAKE_BUILD_TYPE=Release \
		-DGGML_CPU=ON \
		-DGGML_CUDA=OFF \
		-DGGML_CPU_REPACK=ON
	cmake --build $(BUILD_DIR) --target llama-server -j$(JOBS)

llama-server: $(BUILD_DIR)/bin/llama-server
	cp $(BUILD_DIR)/bin/llama-server .

clean:
	rm -rf build
