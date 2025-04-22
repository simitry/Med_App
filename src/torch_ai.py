import torchxrayvision as xrv
import skimage, torch, torchvision

def scan_image(img_thorax):
    """scan the image given and return the ai result"""
    # Prepare the image:
    img = skimage.io.imread(img_thorax)
    img = xrv.datasets.normalize(img, 255) # convert 8-bit image to [-1024, 1024] range
    img = img.mean(2)[None, ...] # Make single color channel

    transform = torchvision.transforms.Compose([xrv.datasets.XRayCenterCrop(),xrv.datasets.XRayResizer(224)])

    img = transform(img)
    img = torch.from_numpy(img)

    # Load model and process image
    model = xrv.models.DenseNet(weights="densenet121-res224-all")
    outputs = model(img[None,...]) # or model.features(img[None,...]) 

    # Print results
    output= dict(zip(model.pathologies,outputs[0].detach().numpy()))

    return output
