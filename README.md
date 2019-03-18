# SCRiBBLE

SCRiBBLE the simple project to show how to use machine learning in the web applications.

Run the project:
```bash
$ export PORT=8080
$ export MONGO_URL=mongodb+srv://<username>:<password>@domain.mongodb.net/<database>?retryWrites=true
$ python app.py
```

The binary model file has been splited by the command:
```bash
$ cd model
$ split -b 50M image224_hash.model image224_hash.model.
```

Project dependencies:
* pytorch 0.4
* asyncio
* aiohttp
* pymongo
    * dnspython

The project prepared for deploying to heroku.

