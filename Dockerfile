# Set the base image
FROM continuumio/miniconda3:4.6.14

# Install linux dependencies
RUN apt update && \
    apt-get update && \
    apt-get install -y gcc build-essential

# ./install | create keeper mining environment
COPY setup/environment-linux.yml setup/
RUN conda env create -f setup/environment-linux.yml

# conda activate keeper mining
RUN echo "source activate $(head -1 setup/environment-linux.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 setup/environment-linux.yml | cut -d' ' -f2)/bin:$PATH

# New files
COPY ./ /app
WORKDIR /app

# Entry
CMD ["/opt/conda/envs/mai2-keeper/bin/python3", "main.py"]
# CMD ["sleep", "86400"]
