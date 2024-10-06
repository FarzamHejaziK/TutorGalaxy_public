# Disclaimer

This repository hosts the code for the **TutorGalaxy** service, originally designed as a backend for [TutorGalaxy.com](https://tutor-galaxy.com). Over time, I will refine and organize the code and the README to make it more user-friendly and adaptable as a package for broader use.

# What is tutor galaxy?
Tutor Galaxy is a personal tutoring service, and its key differentiator from **ChatGPT** is its ability to create and stick to a long-term learning plan for the user. Unlike ChatGPT, which is more focused on short-term interactions, Tutor Galaxy is designed to stay committed to the user's learning plan over time. It has been observed that ChatGPT, even when attempting to plan for a user, tends to deviate from the plan as the conversation progresses. In the following section, we will dive deeper into how Tutor Galaxy addresses the challenge of maintaining commitment to long-term plans. 

# How tutor galaxy works?
The following is the block diagram of the Tutor Galaxy service.
<img width="1972" alt="Screenshot 2024-10-06 at 12 33 36 PM" src="https://github.com/user-attachments/assets/bdd3311d-4f1f-4f4f-b397-146dbca5be39">

# Tutor Initialization Module

To understand the user's expectations, the system starts a conversation to extract the main features the tutor should have from the user's point of view. The primary features the system aims to extract are:

- The topic that the tutor should discuss with the user.
- Whether the tutor should only answer questions or also plan and teach the course to the user.
- The character or personality of the tutor.


# Ongoing Tutor-User Interaction Module

Based on the features extracted in the initialization module, we can now generate a clear system prompt for the tutor. The tutor then starts by understanding the user's preferred teaching style. If the user requests a planned teaching approach, the tutor creates a session plan, edits it based on user feedback, and teaches according to the plan.

The main challenge here is **maintaining focus on the plan, as the user may ask numerous questions during each step. This makes it increasingly difficult for the tutor to stick to the original plan as the conversation becomes lengthy and complex.**

# Long-term Learning and sticking to the plan 






