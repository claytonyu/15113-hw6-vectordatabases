# 15-113 HW9 - Prompt Log
See the `TESTING.md` file for an overview of our generative AI was used in this assignment. Most of this assignment used Claude Sonnet 5.5 on Medium effort. Here are selected prompts I made in this project to generative AI.

## Generating Test Suite
Read the README first before all else. I'm writing tests for three functions, with some tests written already in `tests`. Write a suite of tests, for these three functions only. Check for boundary cases and error cases, as well as anything else that might go wrong.

kmeans clusters vectors based on cosine similarity into k groups.

paper_id removes the version suffix from ArXiV ids, and may fail if given an empty string or an older type of id.

result_line formats each result paper of a search, with proper left padding to the prefix, so that after multiple calls with the same padding amount, the results should have the titles line up horizontally. It may fail if the padding is zero, or perhaps if the number prefix is not as expected.

## Fixing Bugs (originally present in code from HW6)
Some tests are failing. Fix the code in src to make them pass. Don't make changes too complicated.

## Checking GitHub Workflow File
I want to do CI with github. This repo uses pytest. I want to use uv, since it's faster to setup. I also have a requirements.txt to import. Does the tests.yml file work? Don't modify anything; just read.

## Verifier Prompt
The test suite is failing. Make it pass.