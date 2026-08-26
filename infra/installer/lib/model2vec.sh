#!/usr/bin/env bash

BANGI_MODEL2VEC_REPO="minishlab/potion-base-2M"
BANGI_MODEL2VEC_FILES=(config.json model.safetensors modules.json special_tokens_map.json tokenizer.json tokenizer_config.json vocab.txt)
BANGI_MODEL2VEC_DOWNLOAD_MAX_TIME=300

bangi_install_model2vec_model() {
    local model_dir="${BANGI_SHARED_MODEL2VEC_DIR}/potion-base-2M"
    local temp_dir=""
    local file=""

    if [[ -f "${model_dir}/model.safetensors" ]]; then
        bangi_log "model2vec embedding model already installed"
        return 0
    fi

    bangi_log "Downloading model2vec embedding model (${BANGI_MODEL2VEC_REPO})"
    temp_dir="$(mktemp -d)" || bangi_fatal "Cannot create temporary directory for model2vec download"

    for file in "${BANGI_MODEL2VEC_FILES[@]}"; do
        curl -fL --max-time "${BANGI_MODEL2VEC_DOWNLOAD_MAX_TIME}" \
            "https://huggingface.co/${BANGI_MODEL2VEC_REPO}/resolve/main/${file}" \
            -o "${temp_dir}/${file}" \
            || { rm -rf "${temp_dir}"; bangi_fatal "model2vec download failed for ${file}"; }
    done

    install -d -m 0755 -o root -g root "${model_dir}" \
        || bangi_fatal "Cannot create model2vec model directory: ${model_dir}"
    mv -f "${temp_dir}"/* "${model_dir}/" \
        || bangi_fatal "Cannot install model2vec model files"
    rm -rf "${temp_dir}"
}
