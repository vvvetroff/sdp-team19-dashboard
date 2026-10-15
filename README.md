# UConn SDP Team 19 - Dashboard

## Notes for Brandon Lynch

Hello, my name is Vlad Vetroff! Please to meet you, here in this markdown document!

This is the complete repo for our (Esha and I) side of the Turbo Ducks project, where we get the data from the DMS (or otherwise), parse it and display it on a dashboard.

I am sure you have some questions regarding this project, as you and your team are continuing it. I figured I could answer some questions that you MIGHT have. Will you read it? Beats me.

> How do I start this app up?

- `docker compose up -d` at the root of the repo. I do not have the `.env` variables anymore, but thankfully they are fake.
  - `OWL_API_KEY` is just some random string used within `backend/mock/mock_dms.py` and has no real bearing within the project as a whole.
  - `OWL_INSTANCE` is just the url the `mock_dms.py` runs on.
  - `REDIS_HOST` and `REDIS_PORT` are the default host and port of a Redis container. Check the Redis documentation for that.
  - You WILL need to populate these if you want the app to run!
- If you want to run the servers separately (would not recommend).
  - Backend:

    ```sh
    cd backend/
    python3 -m venv .venv
    source .venv/bin/activate # For macs
    source venv/Scripts/activate # For windows (ew)
    pip install --upgrade pip && pip install -r requirements.txt
    ```

  - Frontend:

    ```
    cd frontend/
    npm install
    npm run dev
    ```

    - update packages as needed

> Do you have documentation?

- Whatever documentation you need, you can find it in the contents of the `doc/papers/` dir, especially the last paper.

> What is the tech stack, and why did you choose this particular stack?

- The backend was built with FastAPI + Redis, and frontend with React. Pretty standard stuff.

- Pretty much all of us knew how to program in Python. We didn't want to learn some other language, like Go or Java, to make a backend server, as we had other things going on at the time; being a senior and all. Python, and by extension Flask/FastAPI, was just the most sensible, go-to option at the time.

- We chose to use FastAPI instead of the UConn 'standard' of Flask because of FastAPI's built-in support for WebSockets, which plays a big part in this project, with the whole "real time" display of incoming data and everything. Plus, I have grown to LOVE FastAPI, as I am sure you might/will too!

- There is nothing to say about our choice of React for frontend, other the fact that the most popular charting library `recharts` uses, or at least is used alongside, React. I **highly** recommend you look through the `recharts` documentation, or choose a different charting library, if you so desire.

- The database is a Redis cache, which is an emphemeral cache. I will explain why we chose this in the next question

> Why does this repo not have a persistent database, like PostgreSQL or similar? Why did you choose to use a Redis cache?

- We chose to use a Redis cache for a couple of reasons.
  1. This was a prototype. We were not expected to built a fully fledged app, ready for production for the Formula SAE team, at the time of development. As such, it does not have all the necessary bells and whistles, like OAuth/SAML login with UConn NetID, deployment config and such.
  2. After speaking directly to the Electrical Lead of Formula SAE, I have learned that they already store the data that they collect internally, inside the car's CAN network and inside an SD Card. Therefore, there would be no point in us persisting this data on our end, unless they want to keep another copy of the data.
  3. Formula SAE, at the time of development, did not express the desire to view past data logs in this app. I figured it is because they can already do that, by means of looking at the data from the SD card.
  4. We saw no reason to have persistent data. This app is analogous to a magnifying glass or a multimeter for the electric race car. With respect to this app, Formula SAE cares about what the data looks like right now and what it looked like two minutes ago. Since Formula SAE wanted to keep a record of what the data looked like within the last two minutes, a Redis cache was perfect for this.

> What is the file structure of this repo?

- `backend/`: all the backend-related logic lives here
  - `mock/`: this dir contains a 'mock' DMS. Although we had access to OWL's Ducks and Quackerboards, we did not have access to a DMS. If we did, we didn't bother testing it. All it contains is a server with one endpoint, to generate fake data.
  - `requests/`: these are Bruno requests, meant to test out the backend/redis functionality
  - The entrypoint for the backend server is `app.py`. Bulk of the logic lives in `background_tasks.py` and `endpoints.py`
- `frontend/`: all the frontend-related logic lives here

> Why is there commented-out code about some 'serial' business and 'uncomment this for demo day'?

- This project is a part of a joint team effort between the CSE and ECE departments. The CSE department developed the ML model and the dashboard, while the ECE department developed whatever the hell they developed. Although both departments appeared in our weekly meetings with OWL, hardly did we talk to the ECE department (they won podium!). When it came time to showcase our project for demo day, the ECE department created a 'mock CAN bus' which generated fake data as if it came from the Formula SAE electric vehicle. This fake data would get funneled into and read from a USB-C serial bus. This required seperate code to be developed so that the app could read and parse incoming data from the serial port. This project was intended to perform API calls to an actual DMS to get the data, and thus the commented out code has no real bearing on the project as a whole.

> This code looks so good! I love it! Who developed it?

- Esha and I

> This code looks real BAD! I hate it! Who developed it?

- Esha and I

> This code looks okay. I feel neutral about it. Who developed it?

- Esha and I

> Are you available for any more questions?

- Of course! Just email me at `vladislav.vetroff@gmail.com` or send a friend request on discord; you'll have to email me for my discord username, however.

I hope you and your team can really improve this side of the project, especially the contents of the `frontend/` dir. I am sure you will, as it is a small project, all things considered.
