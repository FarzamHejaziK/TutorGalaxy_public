# Disclaimer

This repository hosts the code for the **TutorGalaxy** service, originally designed as a backend for [TutorGalaxy.com](https://tutor-galaxy.com). Over time, I will refine and organize the code and the README to make it more user-friendly and adaptable as a package for broader use.

## Table of Contents
- [Disclaimer](#disclaimer)
- [What is Tutor Galaxy?](#what-is-tutor-galaxy)
- [How Tutor Galaxy Works](#how-tutor-galaxy-works)
- [Tutor Initialization Agent](#tutor-initialization-agent)
- [Ongoing Tutor-User Interaction Agent](#ongoing-tutor-user-interaction-agent)
- [Long-Term Learning and Sticking to the Plan](#long-term-learning-and-sticking-to-the-plan)
- [Additional Info and Features](#additional-info-and-features)


# What is tutor galaxy?
Tutor Galaxy is a personal tutoring service, and its key differentiator from **ChatGPT** is its ability to create and stick to a long-term learning plan for the user. Unlike ChatGPT, which is more focused on short-term interactions, Tutor Galaxy is designed to stay committed to the user's learning plan over time. It has been observed that ChatGPT, even when attempting to plan for a user, tends to deviate from the plan as the conversation progresses. In the following section, we will dive deeper into how Tutor Galaxy addresses the challenge of maintaining commitment to long-term plans. 

# How tutor galaxy works?
Tutor Galaxy has two conversational agents. The first agent is the Tutor Initialization Agent, which sets up the tutoring process. After that, the Tutor Agent takes over and creates a personalized tutoring session for the user. The following is the block diagram of the Tutor Galaxy service.
<img width="1877" alt="image" src="https://github.com/user-attachments/assets/3eba770d-72d5-4e72-8201-2fda8d321044">





# Tutor Initialization Agent

To understand the user's expectations, the agent starts a conversation to extract the main features the tutor should have from the user's point of view. The primary features the system aims to extract are:

- The topic that the tutor should discuss with the user.
- Whether the tutor should only answer questions or also plan and teach the course to the user.
- The character or personality of the tutor.


# Ongoing Tutor-User Interaction Agent

The Tutor Agent consists of two main sub-agents: the **Planner Agent** and the **Plan Executor Agent**. Based on the features extracted in the initialization phase, the **Planner Agent** starts by understanding the user's preferred learning style and then creates a customized session plan. The Planner Agent continues the tutoring session until the session planning is done and ready to be handed off to the **Plan Executor Agent**.

The **Plan Checker** verifies whether the Planner Agent has completed the session plan and whether the user has approved it before handing off to the Plan Executor Agent. This ensures the tutoring process is aligned with the user's goals and expectations before moving forward.

The **Plan Executor Agent** is responsible for following the developed plan, answering user questions, and maintaining alignment with the session goals.

The main challenge here is **maintaining focus on the plan, as the user may ask numerous questions during each step. This makes it increasingly difficult for the tutor to stick to the original plan as the conversation becomes lengthy and complex.**

<img width="990" alt="image" src="https://github.com/user-attachments/assets/7cd4d7e9-e06a-4e21-a393-2cf153853f06">





# Long-Term Learning and Sticking to the Plan


The main objective of the Plan Executor Agent is to ensure that the tutor stays committed to the long-term learning plan and prevents deviation during the ongoing conversation with the user. It is important to note that the plan has already been extracted by the Plan Checker and is assumed to be fixed. The inputs to the agent include the conversation history, the learning plan, the plan pointer, and the latest user message. The plan pointer indicates the specific topic within the plan that the current conversation is addressing.

The first module in the agent is the **"Next Action Predictor"**, which determines the next best action among the following options:
1. Start a new topic.
2. Continue with the current topic.
3. Answer a user question.
4. Continue answering an ongoing user question.

Once the next action is predicted, the **"Update System Prompt"** module updates the system prompt, and the system responds to the user in alignment with the suggested action. After the system message is generated, the **"Plan Progress Tracker Module"** checks the conversation and updates the plan pointer accordingly.

<img width="1599" alt="image" src="https://github.com/user-attachments/assets/b78afbb4-5943-4cf3-b9e5-00cd5e99db6e">


# Additional Info and Features

Several additional features have been implemented:

1. Recurring payments using Stripe API for user subscriptions.
2. Text-to-speech functionality using Google APIs.
3. Code execution capability for courses where the user requests to learn a programming language.







