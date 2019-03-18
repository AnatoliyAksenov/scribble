import asyncio
from aiohttp import web

import torch
import torchvision.transforms as transforms

import pymongo
import numpy as np
import glob
import tarfile
import os
from io import BytesIO

import PIL
import PIL.Image as Image
import base64
from io import BytesIO

model = None

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])

transform = transforms.Compose([
            transforms.Resize((224, 224)),
            # transforms.Lambda(lambda x: PIL.ImageOps.invert(x)),
            transforms.Grayscale(3),
            transforms.ToTensor(),
            normalize,
        ])


# MongoDB scribbles database
# example url: mongodb+srv://<username>:<password>@domain.mongodb.net/<database>?retryWrites=true
client = pymongo.MongoClient(os.environ.get('MONGO_URL'))
db = client.scribbles


def predict(data):
    # The make a class prediction
    global model
    if not model:
        # model = torch.load("model/image_hash.model")

        # Github has limit to file size at 100M
        # And I have to concat splited files in memory

        b = BytesIO()
        glst = glob.glob("model/*.tar.*")

        # concat in memory
        for t in glst:
            with open(t, "rb") as f:
                b.write(f.read())
        b.seek(0)

        # untar
        with tarfile.TarFile(fileobj=b) as f01:
            for f in f01:
                r = f01.extractfile(f)
        
        # model = torch.load("model/image224_hash.model")
        model = torch.load(r)
        model = model.to('cpu')

    input = prepare(data)

    return model(input)


def prepare(image):
    image = PIL.ImageOps.invert(image)    
    input = transform(image)
    input = input.reshape([1] + list(input.shape))

    return input.to('cpu')

def find_class(data, maxdist=9, top=10):
    # Calculate L2 distnace for each class stored in database
    # and return `top` classes with distnance lower `distnance`

    if db:
        classes = {}
        cursor = db.inventory.find({})
        for obj in cursor:
            classes[obj['class_name']] = obj['res']

        dist = {}
        for c in classes:
            h1 = np.array(classes[c])
            h2 = data
            distance = np.linalg.norm(h1 - h2)
            if distance <= maxdist:
                dist[c] = distance

        keys = sorted(dist, key=lambda x: dist[x], reverse=False)

        return [{x:dist[x]} for x in dist if x in keys][:top]
    
    else:        
        return []


# AIOHTTP HANDLERS


async def pwa(request):
    # Return main page (our pwa application)
    return web.FileResponse("app/index.html")


async def query(request):
    # Predict class
    # Fields in post data:
    # imagedata - URL data (`canvas.toDataURL()`) witch content somthing as it data:image/png;base64,iVBORw0KGgo
    #             The Image format would be PDF. 
    # maxdist - maximal distance between two image hashes
    # top - how match classes have to return

    postdata = await request.post()
    imagedata = postdata['imagedata']
    maxdist = postdata.get('maxdist') or 9
    top = postdata.get('top') or 3

    info, imb64 = imagedata.split(',')
    imb = base64.b64decode(imb64)
    png = Image.open(BytesIO(imb))
    png.load() # required for png.split()

    image = Image.new("RGB", png.size, (255, 255, 255))
    image.paste(png, mask=png.split()[3]) # 3 is the alpha channel


    # print(info, image.size)
    result = predict(image)
    result = result[0].reshape(-1)
    res = [ float(x) for x in list(result.data.numpy().reshape(-1))]
    classes = find_class(res, maxdist, top)


    return web.json_response({
        "result": res,
        "classes": classes,
        "imageinfo": info
        })


async def save(request):
    # Save data to mongodb database
    
    postdata = await request.post()
    class_name = postdata.get('data[class_name]')
    res = postdata.getall('data[res][]')
    res = [float(x) for x in res]

    # TODO: Test an input data
    # {"class_name": "test", "res": res}
    db.inventory.insert_one({"class_name": class_name, "res": res})
    return web.json_response({"result": "OK"})


# AIOHTTP ROUTES
routes = [
    ('GET', '/main',     pwa,  'main'),
    ('POST', '/q',      query, 'query'),
    ('POST', '/save',   save,  'save')
]


if __name__ == "__main__":
    print("test case")
    image = Image.open("test/test3.jpg")
    image = PIL.ImageOps.invert(image)
    
    input = transform(image)

    # Github has limit to file size at 100M
    # And I have to concat splited files in memory

    b = BytesIO()
    glst = glob.glob("model/*.model.*")

    # concat in memory
    for t in glst:
        with open(t, "rb") as f:
            b.write(f.read())
    b.seek(0)

    # untar
    # with tarfile.TarFile(fileobj=b) as f01:
    #     for f in f01:
    #         r = f01.extractfile(f)
    # 
    # model = torch.load("model/image224_hash.model")
    # model = torch.load(r)

    model = torch.load(b)
    
    client = pymongo.MongoClient(os.environ.get('MONGO_URL'))
    db = client.scribbles

    classes = {}
    cursor = db.inventory.find({})
    for obj in cursor:
        classes[obj['class_name']] = obj['res']

    model.eval()

    with torch.no_grad():
        input = input.reshape([1] + list(input.shape))
        output = model(input)
        res = [ float(x) for x in list(output.data.numpy().reshape(-1)) ]

        db.inventory.insert_one({"class_name": "test", "res": res})

        dist = {}
        for c in classes:
            h1 = np.array(classes[c])
            h2 = res
            distance = np.linalg.norm(h1 - h2)
            dist[c] = distance
        print(dist)
