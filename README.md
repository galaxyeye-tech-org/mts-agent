English | [中文](./README_zh.md)

# MTS-Agent

## Introducing

### Overview

Cognitive Engineering-Driven Universal Intelligent Agent (MTS-agent) is an innovative open-source project aimed at integrating the latest large language models (such as GPT-4) with unique cognitive engineering theory to create an advanced AI agent capable of simulating human intelligent behavior. This project is based on a prototypical architecture that comprises perception stream, long-term memory, and execution as its three core elements, deconstructing and replicating the process of human intellectual activities. By endowing GPT with new organizational and procedural intelligence, MTS-agent has crafted an entity that not only understands tasks but is also capable of autonomously advancing the evolution of civilization.

### Background

Current GPT models show limitations in handling complex tasks, particularly lacking in process intelligence, i.e., the inability to simulate the coherent logic and creative tool usage in human problem-solving. The MTS-agent project emerged in response to this challenge, aiming to optimize and transcend traditional task-oriented AI by reflecting on and re-creating the general process of human intellectual activities, establishing a universally intelligent agent capable of logic biomimicry.

### Feature

1. Perception Stream: A component similar to the human stream of consciousness, capable of receiving and processing various sensory information, such as visual and auditory inputs, as well as internal thoughts.
2. Long-term Memory: Provides a structure for continuity across time and accumulation of knowledge, enabling AI to save and utilize previous experiences and learning.
3. Execution and Working Memory: Allows AI to perform actions based on current tasks and internal states (long-term memory and perception stream).
4. Deconstructing Human Intellectual Activities: By studying how humans think, solve problems, and create tools, the project has constructed paths of execution for the intelligent agent.
5. Multi-role Model: Simulates multiple human thought roles within the perception stream, such as the curious, the solver, and the predictor, mimicking free thoughts and generating processes to solve problems.

![Figure 1: Conversations without prior experience](doc/pic/对话2.png)

<center>Figure 1: Conversations without prior experience</center>


![Figure 2: Combining experience in conversation and actively enhancing effects](doc/pic/对话1.png)

<center>Figure 2: Combining experience in conversation and actively enhancing effects</center>

### Progress

At the prototype stage, the project has achieved the construction of core structures and basic functionalities:

- Implemented API encapsulation for attention marking, information classification, and multi-role dialogue models based on GPT.
- Built a long-term memory model, including forgetting and awakening mechanisms as well as multi-tiered storage systems, optimizing search efficiency and storage.
- Developed dialogue generation API, supporting the integration of working memory in dialogue tasks and free-thought interactions.
- Initially integrated the structures of knowledge and policy memory, providing the AI with the capability to think and execute tasks based on stored strategies.

### Goals

The short-term goal is to enhance the performance of the current prototype and commercialize it in specific domains, providing professional-level services in areas such as psychological counseling, health, etc. The long-term goal is to inherit and develop the emotional decision system in the "Thought Engineering" theory, further improving the intelligent agent's autonomous thinking and motivation formation, enabling it to become an intelligent individual capable of independently advancing civilization.

### Participation and Contributions

The mts-agent project encourages open-source developers and researchers in the science of thinking to participate, and it maintains an open attitude towards all contributors' code and ideas. Project maintainers look forward to collaborating with global developers and scientific researchers to jointly push forward the future development of humanity and AI technology.

### Design

In the MTS-agent, the perception stream acts as the data hub, facilitating the transfer of information among various roles, as illustrated in the diagram below.
![Figure 3：The structure of the system](doc/pic/感知流.png)

<center>Figure 3：The structure of the system</center>

#### Project File Structure

```
mts-agent
├─ LICENSE
├─ README.md
├─ README_zh.md
├─ data
├─ db
├─ doc              
├─ docker-compose.yml
├─ environment.yml
├─ platform
│  ├─ agents
│  │  ├─ base
│  │  │  ├─ agent_http
│  │  │  ├─ agent_public
│  │  │  ├─ agent_storage_client
│  │  │  ├─ attention_client
│  │  │  ├─ bashrc.sh
│  │  │  ├─ environment.yml
│  │  │  ├─ large_model_client
│  │  │  ├─ mts_agent_service.py
│  │  │  ├─ service
│  │  │  └─ thoughts_flow_client
│  │  ├─ classific_service
│  │  ├─ config
│  │  ├─ convergence_service
│  │  ├─ dialogue_service
│  │  ├─ divergence_service
│  │  ├─ docker-entrypoint.sh
│  │  ├─ main.sh
│  │  ├─ plant_cognition_service
│  │  ├─ requirements.txt
│  │  ├─ response_service
│  │  ├─ second_expression
│  │  ├─ services_main.py
│  │  ├─ setting.py
│  │  ├─ strategy_service
│  │  └─ summarize_service
│  ├─ ai_dialogue_service
│  ├─ front
│  │  ├─ README.md
│  │  ├─ default.conf
│  │  └─ mts_agent_web
│  └─ rag
│     ├─ config
│     ├─ controller
│     ├─ docker-entrypoint.sh
│     ├─ gunicorn.config.py
│     ├─ main.py
│     ├─ model
│     ├─ requirements.txt
│     ├─ service
│     └─ setting.py
├─ scripts
├─ setup.bat
└─ setup.sh


```

### Deploy

The services and middleware can be directly launched through the docker-compose.yml located in the root directory. The official Linux images for the three services are available at https://hub.docker.com/u/galaxyeyetech

For further development or other platforms that require manual compilation, this can be achieved through the Dockerfile files located in the project directories:
/platform/agents/Dockerfile
/platform/rag/Dockerfile
/platform/ai_dialogue_service/Dockerfile

Both rag and ai_dialogue_service support configuration via environment variables, which can be done through .env files or the docker-compose.yml. The docker-compose.yml defines the mts-agent-network network, with network connections using aliases.
Most configurations can be left as default. In the docker-compose.yml, search for OPENAI_API_KEY. This configuration needs to be changed to the user's own APIKEY.

### Usage

To start the agent, use the following command:
`docker compose up -d`

In a web browser, access the deployed server's IP, for example, http://127.0.0.1/. In the tool page, there is a websocket connection address, which by default is `ws://localhost/mts_agent/dialogue/v1/dialogue`. Please change `localhost` to the deployed IP address.
