# Module 3 Exercise: Expanding to Continuous Delivery (CD)

In the labs, we created a CI pipeline that lints code, runs unit tests, and builds a Docker image.
However, it just builds the image and throws it away! It doesn't save it anywhere.

## The Challenge

Your task is to take the pipeline we built in the labs (`ci.yml`), copy it into this `exercise/` folder, and expand it into a **Continuous Delivery (CD)** pipeline.

You need to modify the `build` job so that instead of just building the Docker image locally, it **logs into Docker Hub** and **pushes the image** to a remote registry.

**Requirements:**
1. Add a step *before* the Docker build step that logs into Docker Hub. You should use the official `docker/login-action@v2` action.
2. You will need to provide your Docker Hub username and a Personal Access Token (PAT). In GitHub Actions, you do this using **Secrets**. In your YAML file, reference the secrets using the syntax: `${{ secrets.DOCKERHUB_USERNAME }}` and `${{ secrets.DOCKERHUB_TOKEN }}`.
3. Modify the `docker build` command to tag the image with your Docker Hub username (e.g., `username/my-python-api:latest`) and then run `docker push` to upload it.

*Note: Since you are writing this locally and not in an actual GitHub repository, you don't need to actually run it. Just write the correct YAML syntax!*

Good luck! Check the `solution/` folder for the answer key.
