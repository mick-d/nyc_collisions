from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import Required
from bokeh.plotting import figure
from bokeh.embed import components
import requests
import simplejson as json
import geojson
import json
from geojson import Feature, FeatureCollection
import pandas as pd
from pandas.tseries.offsets import DateOffset
import os

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'this should be a very secret key'
bootstrap = Bootstrap(app)
moment = Moment(app)
#csrf = CsrfProtect()
#csrf.init_app(app)
features={'Volume': 'Volume', 'Adj. Volume': 'Adjusted Volume',
          'Close': 'Closing price', 'Adj. Close': 'Adjusted closing price'}
histories={'last_1m': 1, 'last_6m': 6, 'last_12m': 12}

class StockForm(Form):
    name = StringField('Which stock do you want information on?', validators=[Required()])
    feature = RadioField('Which record do you want to see?',
                         choices=[('Volume', 'Volume'), ('Adj. Volume','Adjusted Volume'),
                                  ('Close', 'Closing price'), ('Adj. Close', 'Adjusted closing price')],
                         default='Volume')
    history = RadioField('How much of the available data history do you want to view?',
                         choices=[('last_1m', 'Last month'), ('last_6m', 'Last 6 months'),
                                  ('last_12m', 'Last 12 months')],
                         default='last_1m')
    submit = SubmitField('Submit')

boom_data_all = pd.read_csv('../../nyc_collisions_data/longlat_filt.csv')
boom_data_ped = pd.read_csv('../../nyc_collisions_data/longlat_filt_ped.csv')
boom_data_bike = pd.read_csv('../../nyc_collisions_data/longlat_filt_bike.csv')
manh_netw_data = pd.read_csv('../../nyc_collisions_data/nyc_intersections_MAN.csv')
manhclean_netw_data = pd.read_csv('../../nyc_collisions_data/nyc_intersections_MAN_clean.csv')
boro1_netw_data = pd.read_csv('../../nyc_collisions_data/nyc_intersections_boro1.csv')
boom_data = boom_data_all
#boom_data_all = boom_data_all.ix[:5000]
#with open('js/boom100.json', 'w') as geojson_file:
    #geojson_file
    #geojson_file.write('collisions = [')
    #json.dump(geo_boom, geojson_file)
    #geojson_file.write('];')
geo_boom_all = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"NUMBER OF PERSONS INJURED": n_inj,
                                                                                 "NUMBER OF PERSONS KILLED": n_kill})
            for p_long, p_lat, n_inj, n_kill in zip(boom_data_all['LONGITUDE'], boom_data_all['LATITUDE'],
                                                    boom_data_all['NUMBER OF PERSONS INJURED'], boom_data_all['NUMBER OF PERSONS KILLED'])])

geo_boom_ped = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"NUMBER OF PERSONS INJURED": n_inj,
                                                                                 "NUMBER OF PERSONS KILLED": n_kill})
            for p_long, p_lat, n_inj, n_kill in zip(boom_data_ped['LONGITUDE'], boom_data_ped['LATITUDE'],
                                                    boom_data_ped['NUMBER OF PERSONS INJURED'], boom_data_ped['NUMBER OF PERSONS KILLED'])])

geo_boom_bike = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"NUMBER OF PERSONS INJURED": n_inj,
                                                                                                        "NUMBER OF PERSONS KILLED": n_kill})
            for p_long, p_lat, n_inj, n_kill in zip(boom_data_bike['LONGITUDE'], boom_data_bike['LATITUDE'],
                                                    boom_data_bike['NUMBER OF PERSONS INJURED'], boom_data_bike['NUMBER OF PERSONS KILLED'])])

geo_manh_netw = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"Borough": 'Manhattan'})
                                   for p_long, p_lat in zip(manh_netw_data['Lon'], manh_netw_data['Lat'])])

geo_manhclean_netw = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"Lon": p_long, "Lat": p_lat})
                                        for p_long, p_lat in zip(manhclean_netw_data['Lon'], manhclean_netw_data['Lat'])])

geo_boro1_netw = FeatureCollection([geojson.Feature(geometry=geojson.Point((p_long, p_lat)), properties={"Lon": p_long, "Lat": p_lat})
                                        for p_long, p_lat in zip(boro1_netw_data['Lon'], boro1_netw_data['Lat'])])

@app.route('/')
def main():
    return redirect('/index')

@app.route('/map')
def map():
    return render_template('map_layers_clusters.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route("/geojson_all", methods=["GET", "POST"])
def get_geojson_all():
    return geojson.dumps(geo_boom_all)

@app.route("/geojson_ped", methods=["GET", "POST"])
def get_geojson_ped():
    return geojson.dumps(geo_boom_ped)

@app.route("/geojson_bike", methods=["GET", "POST"])
def get_geojson_bike():
    return geojson.dumps(geo_boom_bike)

@app.route("/geojson_manh_netw", methods=["GET", "POST"])
def get_geojson_manh():
    return geojson.dumps(geo_manh_netw)

@app.route("/geojson_cleanmanh_netw", methods=["GET", "POST"])
def get_geojson_cleanmanh():
    return geojson.dumps(geo_manhclean_netw)

@app.route("/geojson_boro1_netw", methods=["GET", "POST"])
def get_geojson_boro1():
    return geojson.dumps(geo_boro1_netw)

@app.route('/index', methods=['GET', 'POST'])
def index():
    name = None
    form = StockForm()
    print form.errors
    if form.validate_on_submit():
        session['stock_name'] = form.name.data
        session['feature'] = form.feature.data
        session['history'] = form.history.data
        return redirect(url_for('bokeh_plot'))
    return render_template('index_bs.html', form=form, name=name)

@app.route('/stock_plot')
def bokeh_plot():
    name = session.get('stock_name')
    feature = session.get('feature')
    feature_name = features[feature]
    history = session.get('history')
    n_months = histories[history]
    stock_json_file = requests.get('https://www.quandl.com/api/v1/datasets/WIKI/' +
                                   name + '.json?api_key=xDbkv2XztyErqMSjJ8He')
    stock_dict = stock_json_file.json()
    if 'error' in stock_dict:
        return render_template('error_bs.html', error_message=stock_dict['error'])
    df = pd.DataFrame(stock_dict['data'])
    df.columns=stock_dict['column_names']
    df['Date'] = pd.to_datetime(df['Date'])
    min_date = max(df['Date']) - DateOffset(months=n_months)
    stock_indices = df.loc[:,'Date']>=min_date
    stock_plot = figure(x_axis_type = "datetime")
    stock_plot.line(df.loc[stock_indices,'Date'], df.loc[stock_indices,feature], color='#1F78B4', legend=name)
    #stock_plot.line(dates, choam, color='#FB9A99', legend='CHOAM')
    stock_plot.title = feature_name + " of stock " + name
    stock_plot.grid.grid_line_alpha=0.3
    script, div = components(stock_plot)
    return render_template('bokeh_plot_bs.html', script=script, div=div, stock_name=name)

if __name__ == '__main__':
    app.run(debug=True, port=8000, use_reloader=True)
    #port = int(os.environ.get("PORT", 5000))
    #app.run(host='0.0.0.0', port=port)
