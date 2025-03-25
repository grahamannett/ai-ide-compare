# AI IDE Compare

This is an attempt at comparing the various AI IDE's in a standardized way along a number of axes.

# Setup

This project relies heavily on [mise](https://github.com/jdx/mise) to automate various aspects of the running and collation

# Tasks

Currently there are greenfield and brownfield tasks.

## Greenfield

Greenfield tasks are projects that should start with ideally just a prompt or a minimal amount of information with the intent of evaluating how well the IDE/model does on generating the complete working app. These tasks ideally will be language agnostic such that the IDE/model can be evaluated for various project types/frameworks. This is done as evaluating the AI IDE from a blank slate project that is python based seems to give a lot more information about parts of the IDE (i.e. is it using the appropriate tooling from uv) compared to a similar evaluation for nextjs.

The base folders contain a mise file that contains the prompt for the task that should be used to generate the project.

## Brownfield

Brownfield tasks are not yet implemented, but they should include tasks that are similar to tasks that might be seen in SWE-Bench or similar benchmarks. These tasks will be one off projects and will be language specific but require the AI IDE to implement a feature or fix a bug that we can evaluate with a unit test.

# Running

The goal is to have tasks run using MCP (or if there is another approach) but there are currently no MCP servers that allow this functionality to programmatically kick off one of the project and evals (perhaps something like [buga-luga-cursor-mcp](https://opentools.com/registry/buga-luga-cursor-mcp) but I did not really look too far into it).
Until there is a way to programatically run a task (meaning feed the prompt to the IDE and have it run), running the project task is done manually by opening the directory with the IDE and using the prompt from the `.mise.{MODEL_NAME}.toml` file:

```bash
mise run ide:cursor tasks/greenfield/todo-app
# in the new IDE window, you should be able to see the prompt with the following command:
echo -e $AI_IDE_PROMPT
```

With the new IDE window, follow the instructions from the mise task (which requires pasting the prompt into the chat portion).

Once the IDE chat is done generating the task, the evaluation can be run with `mise run eval tasks/greenfield/todo-app` (which is essentially just `uv run ai-ide-compare tasks/greenfield/todo-app`). This will output the results to the console:

```json
{
  "total_files": 1,
  "total_lines": 1,
  "files_by_type": {
    ".py": 1
  },
  "file_details": [
    {
      "path": "app.py",
      "lines": 1,
      "type": ".py"
    }
  ],
  "ignored_files_count": 0
}
```

# Evaluation

Currently the evaluation looks at lines of code, files and tests if they exist.
