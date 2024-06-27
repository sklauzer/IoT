# IoT
## Data Engineering
The starting point for this project is the sensor values of the CO2 traffic lights at Karlsruhe University of Applied Sciences. For the scope of the project, we were given data from a building for a specific period of time. There is a file for each day and each room. These files are all located in `data/hka-aqm-n`. We have set up a data pipeline to process the data and merge all the individual files. 

You can execute `python utils/data_pipeline.py` for this purpose. All individual files are merged, cleaned, features added and saved. 

In the Data Pipeline we also add external weather data to the dataset. This data is requested from OpenMeteo (https://open-meteo.com/).
You can find the code regarding the weather data in `utils/weather.py`.

Furthermore we have a script to fetch room information from the HKA API. We use this data to display the room name, faculty and room type in the dashboard. When you run `data_pipeline.py`,after the data is saved, the room information gets fetched and saved.

# Data Exploring
The data is then explored in the `Notebooks` folder. We have a notebook for the data exploration: `Data_Exploring.ipynb`

# Dashboard
The dashboard is created with streamlit. You can run the dashboard with `python -m streamlit run Dashboard/Rooms.py`.
We devided the dashboard into three parts: Room page, Floor page and a page to demonstrate the neural net.

# Neural Net
We have a neural net to predict the average tmp value of a day based on the last six days. You can find the architecture of the neural net in `NeuralNetworks/base_class.py`. The neural net is trained in the `Notebooks/neural_net.ipynb` notebook. The neural net (with scalers and encoders) is then saved to `NeuralNetworks/models` where each model is named after the time it finished training. In this model folder you can find the model itself, the encoder and the scalers.

The model is demonstrated in the dashboard to predict the average tmp value of a day. You can upload 6 consecutive files of data for one room, and the model will predict the average tmp value of the next day.