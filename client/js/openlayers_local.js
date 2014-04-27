var hsi;
/*
HSIFind 0.8 BETA
BUILD DATE: 04/02/2013
Smith, Alexander, JPL 2013
Alexander.Smith@jpl.nasa.gov

MODIFY var serv10n_serverBase without a following slash to match the 
server where you have the service running i.e.: 
var serv10n_serverBase = 'http://mipldevwebify1:18080';

Note that if you have serv10n mapped to another subdirectory structure than /service/hsifind 
You may have to modify var hsi below on line 11:
    hsi = new hsiFind(serv10n_serverBase+'/service/hsifind/','map');
*/
var serv10n_serverBase = 'http://mipldevwebify1:18080';
$(document).ready(function(){
    hsi = new hsiFind(serv10n_serverBase+'/service/hsifind/','map',true);
});

var hsiFind = function(urlbase,map_elem_id,singleModeFlag){
    if(urlbase[urlbase.length-1] != '/') urlbase += '/';
    this.hsibase = urlbase; //url base
    this.hsi_service_base; //service base for file results
    this.hsi_active = []; //array of active layers in the map
    this.scroll_index = 0;//index of scrolling (image thumbs) if there are multiple base maps.
    this.hsi_version_name = 'hsifind'; //version name of serv10n
    this.isDragging = false; //tells us if we're dragging a spectra or not
    this.is_popstate = false; //tells us if we're navigating through time...
    this.cachedResults = {}; //holds cached results that we dont need to load again...
    this.singleSlideMode = typeof singleModeFlag != "undefined" ? singleModeFlag : false; //if we want to only see 1 slide, and not load a ton to link it into native systems, just pass in the boolean option.
    var base = this.hsibase.split('/');
    base.pop();base.pop();base.pop();
    base = base.join('/');
    if(base[base.length-1] != '/'){
        base +='/';
    }
    if(this.singleSlideMode){
        //if we are just viewing 1 single spectra, just treat it as such.
        $('#thumbs').hide();
    }
    this.hsi_service_base = base;
    this.iconSize = new OpenLayers.Size(21,25);
    this.iconOffset = new OpenLayers.Pixel(-(this.iconSize.w/2), -this.iconSize.h);
    this.icon = new OpenLayers.Icon('http://www.openlayers.org/dev/img/marker.png', this.iconSize, this.iconOffset);
    this.map = new OpenLayers.Map(map_elem_id,{});
    this.markers = new OpenLayers.Layer.Markers( "Markers" );
    this.allMarkers = []; //array that holds all the markers we might want to make...
    this.map.addLayer(this.markers);
    //for shift + click overrides we use a control
    var that = this;
    var control = new OpenLayers.Control();
    OpenLayers.Util.extend(control, {
        draw: function () {
            // this Handler.Box will intercept the shift-mousedown
            // before Control.MouseDefault gets to see it
            this.box = new OpenLayers.Handler.Box( control,
                {"done": this.unclicked},
                {keyMask: OpenLayers.Handler.MOD_SHIFT});

            this.box.activate();
        },
        zoomBox:function(e){
            alert('zbox')
        },
        unclicked: function (bounds) {

            //OpenLayers.Console.userError(bounds);
            //alert('bounds')
            console.log('bounds',bounds)
            if(typeof bounds.x != "undefined" && bounds.__proto__.CLASS_NAME == "OpenLayers.Pixel"){
                
                var ltln = that.map.getLonLatFromPixel(bounds);
                //console.log('bounds typeof ',typeof ltln.x, ltln)
                if(typeof ltln.lat == "number" && typeof ltln.lon == "number"){
                    var marker = new OpenLayers.Marker(ltln,that.icon.clone());
                    marker.markerIndex = that.allMarkers.length;
                    that.allMarkers.push(marker);
                    that.markers.addMarker(marker);
                    //console.log('allmarkers',that.allMarkers)
                    //now make the new URL
                    
                    
                    var pointStr = '[';
                    $.each(that.allMarkers,function(i,marker){
                        //convertToRange hates the input range [90,-90] so we get the opposite #
                        var l = marker.lonlat.lat < 0 ? Math.abs(marker.lonlat.lat) : -marker.lonlat.lat;

                        var x = Math.round(convertToRange(marker.lonlat.lon,[0,that.clickWidth/8],[0,that.clickWidth]));
                        var y = Math.round(convertToRange(l,[-that.clickHeight/16,that.clickHeight/16],[0,that.clickHeight]));
                        console.log('xy is ',typeof x, typeof y,l,ltln)
                        if(typeof x == "number" && typeof y == "number"){
                            if(i == that.allMarkers.length-1){
                                pointStr += y+'.'+x+']';
                            }
                            else{
                                pointStr += y+'.'+x+',';
                            }
                        }
                    });

                    that.retrieveClick('shiftClick',that.map.baseLayer.name,pointStr,null);
                }
                that.hideLibrary();
            }
        }
    });
    this.map.addControl(control);
    
    this.map.events.register("click", this.map , function(e){
        console.log('exy',e.xy,e)

        if(!e.shiftKey){
            //we dont worry about shift + clicks here they are done by the controls override
            var ltln = that.map.getLonLatFromPixel(e.xy);
            //convertToRange hates the input range [90,-90] so we get the opposite #
            var l = ltln.lat < 0 ? Math.abs(ltln.lat) : -ltln.lat;

            var x = Math.round(convertToRange(ltln.lon,[0,that.clickWidth/8],[0,that.clickWidth]));
            var y = Math.round(convertToRange(l,[-that.clickHeight/16,that.clickHeight/16],[0,that.clickHeight]));
            that.clearMarkers();
            that.retrieveClick('left',that.map.baseLayer.name,x,y);
            that.hideLibrary();
        }
    });
    this.all_imgs = []; //holds all available base images...
    this.init();
}
hsiFind.prototype.projectXyToLatLon = function(x,y){
    var that = this;
    //converts an XY relative to the image into a latlon which is used by the map
    var x = convertToRange(x,[0,that.clickWidth],[0,that.clickWidth/8]);
    var y = convertToRange(y,[0,that.clickHeight],[that.clickHeight/16,-that.clickHeight/16]);
    return {x:x,y:y}
}
hsiFind.prototype.addNewMarker = function(x,y){
    var latlon = new OpenLayers.LonLat(x,y);
    if(!isNaN(latlon.lon) && !isNaN(latlon.lat)){
        var marker = new OpenLayers.Marker(latlon,this.icon.clone());
        this.markers.addMarker(marker);
        this.allMarkers.push(marker);
    }
}
hsiFind.prototype.checkUrl = function(){
    var urlvars = this.getUrlVars();
    if(typeof(urlvars['cube']) != "undefined" && typeof urlvars['spectra'] != "undefined"){
        //we are sharing
        var cube = urlvars['cube'].replace('#','');
        var spectra = urlvars['spectra'].replace('#','');
        $('img[rel="'+cube+'"]').trigger('click');
        this.retrieveLibraryResult(spectra,cube);
    }
    else if(typeof(urlvars['cube']) != "undefined" && typeof(urlvars['spectra']) == "undefined"){
        var cube = urlvars['cube'].replace('#','');
        $('img[rel="'+cube+'"]').trigger('click');
    }
}
hsiFind.prototype.addMarkersOnNewResult = function(){
    //console.log('markers needed, ',urlvars,urlvars['spectra'].indexOf(urlvars['cube']))
    var that = this;
    var urlvars = this.getUrlVars();
    if(urlvars['spectra'].indexOf(urlvars['cube']) != -1){
        //its a match, lets display markers
        var points = [];
        var p = urlvars['spectra'].split('[')[1];
        p = p.split(']')[0];
        p = p.split(',');
        $.each(p,function(i,pt){
            var point = {x:pt.split('.')[1],y:pt.split('.')[0]};
            var xy = that.projectXyToLatLon(point.x,point.y)
            that.addNewMarker(xy.x,xy.y);
            console.log('adding new marker',xy)
        })

    }   
}
hsiFind.prototype.getUrlVars = function(){
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}
hsiFind.prototype.init = function(){

    var url = this.hsibase+'/list_cubes/null/null/null';
    var that = this;
    that.showLoading();
    this.results = {};//new object to hold cached results
    $.ajax({
        url:url,
        cache:true,
        type:"get",
        dataType:"jsonp",
        success:function(d){
            that.hsi_version_name = d.application;
            $('#vname').html(that.hsi_version_name);
            var images = d.result.stdout.split("\n");
            var basemap = d.result.files[0];
            $.each(images,function(i,x){
                
                if(x.length > 5){
                    that.all_imgs.push(x);
                }
            });
            that.getBaseMap(that.all_imgs);
        }
    });
    //ok first we should append our slider for the layer opacity
    $('#map').append('<div id="opacityRange"><label for="oprg">Overlay Opacity</label><input id="oprg" type="range" value="1.0" min="0" max="1" step="0.1" /></div><div id="accrualNav" />');
    this.initClickListeners();

}

hsiFind.prototype.getBaseMap = function(images){
    
    var that = this;
    var urlvars = that.getUrlVars();
    $.each(images,function(i,x){
        
        var url = that.hsibase+'get_cube/'+x+'/0/0';
        if(typeof that.cachedResults[url] == "undefined"){
            $.ajax({
                url:url,
                type:"get",
                cache:true,
                dataType:"jsonp",
                success:function(d){
                    handleResult(d);
                }
            });
        }
        else{
            handleResult(that.cachedResults[url])
        }
        function handleResult(d){
        if(d.result){
            that.results[x] = d;

            if(i == 0 && typeof(urlvars['cube']) == "undefined") that.setBaseMap(d.result.files[4],x);
            if(typeof(urlvars['cube']) != "undefined"){
                //ok create markers if we see that we need to
                //alert(' markers')

                if(x == urlvars['cube'].replace('#','')) that.setBaseMap(d.result.files[4],x);
            }
                
            if(i == images.length-1){
                //were at the end, generate thumbs
                //ALSO, CHECK TO SEE IF WE EVEN WANT TO GET ALL THE BASELAYERS. I MAY BE THE TYPE TO SAY NAY
                if(!that.singleSlideMode){
                    setTimeout(function(){
                        that.getAllBaseLayers();
                    },1000);
                }
            }
        }
    }
    });

}
hsiFind.prototype.setBaseMap = function(bm_img,img_name){
    $('#share').fadeOut();

    var options = {numZoomLevels: 21,isBaseLayer:true};
    var that = this;
    var img = $('<img />');
    var b_img = bm_img.replace(that.hsi_service_base,'');
    img.attr('src',that.hsi_service_base+b_img);
    var urlvars = that.getUrlVars();
    img.load(function(){

        var w = this.width/2;
        var h = this.height/2;
        var quarter_h = h / 8;
        var quarter_w = w / 8;
        var half_h = h / 4;
        var half_w = w / 4;
        var layer = new OpenLayers.Layer.Image(
                img_name,
                that.hsi_service_base+b_img,
                new OpenLayers.Bounds(0, -quarter_h, half_w, quarter_h),
                new OpenLayers.Size(w,h),
                options
            );
        that.results[img_name].origWidth = w*2;
        that.results[img_name].origHeight = h*2;
        //layer.origHeight = h;
        that.clickWidth = w*2;
        that.clickHeight = h*2;
        if(that.map.baseLayer == null && typeof urlvars['cube'] != "undefined")
            setTimeout(function(){that.checkUrl();},300);
        that.map.addLayer(layer);
        that.map.setBaseLayer(layer)
        that.map.zoomToMaxExtent();
        that.map.setLayerIndex(layer,0);
        that.markers.setZIndex(50000);
        if(typeof(that.getUrlVars()['cube']) == "undefined") that.hideLoading();
        if(typeof(that.getUrlVars()['cube']) != "undefined" && typeof(that.getUrlVars()['spectra']) == "undefined")
                that.hideLoading();
    })
    
}
hsiFind.prototype.addMapLayer = function(url,name){
    var that = this;
    var options = {numZoomLevels: 20,isBaseLayer:false};
    //needs to get image size and make layer size appropriately...
    var img = $('<img />');
    img.attr('src',url);
    img.load(function(){
        var w = this.width/2;
        var h = this.height/2;
        var quarter_h = h / 8;
        var quarter_w = w / 8;
        var half_h = h / 4;
        var half_w = w / 4;
        var layer = new OpenLayers.Layer.Image(
            name,
            url,
            //new OpenLayers.Bounds(0, -90, 240, 90),
            new OpenLayers.Bounds(0, -quarter_h, half_w, quarter_h),
            //new OpenLayers.Size(640,480),
            new OpenLayers.Size(w,h),
            options
        );
        that.hsi_active.push(layer);
        that.map.addLayer(layer);

        that.markers.setZIndex(50000);

        /*that.map.setLayerIndex(layer,1)
        that.map.setLayerIndex(that.markers, 299);*/
        setTimeout(function(){
            that.hideLoading();
        },1000)
    })
    
}
hsiFind.prototype.showLibrary = function(){
    var that = this;
    var ph = $('.spectrum_pane').height();
    $('.spectrum_pane').addClass('show_library');
    setTimeout(function(){
        that.retrieveSpectralLib();
    },250);
}
hsiFind.prototype.hideLibrary = function(){
    $('.spectrum_pane').removeClass('show_library');
}
hsiFind.prototype.retrieveLibraryResult = function(spectra_id,base_id,is_popstate){
    var that = this;
    this.removeShiftClickButton();
    var popstate = typeof is_popstate == "undefined" ? false : is_popstate;
    var urlVars = this.getUrlVars();
    //check if there is a continuum
    
    if(typeof urlVars['continuum'] != "undefined") urlVars['continuum'] = urlVars['continuum'].replace('/','');
    console.log('urlvars',urlVars,urlVars['continuum'])
    var sharable_url = typeof urlVars['continuum'] == "undefined" ? '?cube='+base_id+'&spectra='+spectra_id : '?cube='+base_id+'&spectra='+spectra_id+'&continuum='+urlVars['continuum'];
    //if(spectra_id.indexOf(base_id) == -1) this.clearMarkers();
    this.clearMarkers();
    $('#share a').attr('href',sharable_url);
    var pushObj = typeof urlVars['continuum'] == "undefined" ? {cube:base_id,spectra:spectra_id} : {cube:base_id,spectra:spectra_id,continuum:urlVars['continuum']};
    if(!popstate) history.pushState(pushObj,'hsifind',sharable_url);
    $('#share').fadeIn();

    var url = typeof urlVars['continuum'] == "undefined" ? this.hsibase+'search/'+base_id+'/'+spectra_id+'/0' : this.hsibase+'search/'+base_id+'/'+spectra_id+'/'+urlVars['continuum'];
    var that = this;
    that.showLoading();
    if(typeof that.cachedResults[url] == "undefined"){
        console.log("CACHED RESULT UNDEFINED",that.cachedResults,url)
        $.ajax({
            url:url,
            type:'get',
            cache:true,
            dataType:'jsonp',
            success:function(d){
                handleResult(d);
            }
        });
    }
    else{
        handleResult(that.cachedResults[url])
    }
    //inline method for results
    function handleResult(d){
        if(d.result && d.result.stderr.indexOf('ValueError: total size of new array must be unchanged') == -1 && d.result.stderr.indexOf('Cannot find') == -1){
                that.cachedResults[url] = d;
                $.each(that.hsi_active,function(i,x){
                    that.map.removeLayer(x);
                });
                that.hsi_active = [];

                var out_map = that.hsi_service_base+d.result.files[0];
                //that.addMapLayer(out_map,'map overlay');
                //REMOVED ABOVE addMapLayer
                var superpixel = that.hsi_service_base+d.result.files[1];
                that.addMapLayer(superpixel,'superpixel');
                var spectrum = that.hsi_service_base+d.result.files[2];
                var multiband_indicator = spectra_id.indexOf('MULTIBAND') >= 0 ? 'multiband' : 'nonmultiband';
                
                //DEPRECATED WITH THE NEW NVD3 LIBRARY:: 
                //$('#spec_img').html('<div id="save_icon"></div><img class="draggable_image '+multiband_indicator+'" data-hsi-ref="'+spectra_id+'" src="'+that.hsi_service_base+d.result.files[3]+'" />');
                var obj = {label:'Original: ['+spectra_id.split('[')[1],data:d.result.stdout};
                if(d.result.stdout.length > 1000){
                    that.makeChart([obj]);
                    that.spectraBase = obj;
                }
                $('#spec_img svg').attr('data-imgurl',that.hsi_service_base+d.result.files[3])
                $('#spec_img svg').attr('data-hsiref',that.getUrlVars()['spectra']);
                $('#spec_img svg').addClass('draggable_image');
                //$('#specSvg').attr('data-')
                $('#spectrum h3').html('Spectrum for '+that.map.baseLayer.name+' <a href="#">Hide</a>');
                $('#spectrum').addClass('spec_showing');
                that.addMarkersOnNewResult();
                that.initjQueryUI();
            }
            else if(d.result && d.result.stderr.indexOf('ValueError: total size of new array must be unchanged') >= 0){
                alert('Error: Bands do not match')
                //console.log(d.result.stderr)
                that.hideLoading();
            }
            else if(d.result && d.result.stderr.indexOf('Cannot find') != -1){
                alert('Error: Bad Input, Please Correct and Try again.')
                //console.log(d.result.stderr);
                that.hideLoading();
            }
    }
}
hsiFind.prototype.clearMarkers = function(){
    var that = this;
    $.each(this.allMarkers,function(i,marker){
        that.markers.removeMarker(marker);
        
    })
    that.allMarkers = [];
}
hsiFind.prototype.removeShiftClickButton = function(){
    $('#accrualNav').html('');
}
hsiFind.prototype.shiftClickUpdate = function(type){
    if($('#accrualNav .navButton').length == 0){
        console.log('updateing shift click button')
        $('#accrualNav').html('<div class="navButton" data-count="0" id="cancelbutton">Cancel</div><div id="gobutton" class="navButton">Go!</div>')
    }
    if(type == 'popstate'){
        var ps = parseInt($('#cancelbutton').attr('data-count'))-1;
        $('#cancelbutton').attr('data-count',ps);
    }
    else{
        var ps = parseInt($('#cancelbutton').attr('data-count'))+1;
        $('#cancelbutton').attr('data-count',ps);
    }
}
hsiFind.prototype.retrieveClick = function(clickType,resource_name,x_click,y_click){
    //NOTE: If clickType is shiftClick we pass in our multiple point string in as x_click
    
    //call get_spectrum_data like this
    //http://mipldevwebify1:18080/service/hsifind/get_spectrum_data/VIR_IR_1B_1_394683501_1.QUB[13.96,25.196]/VIR_IR_1B_1_394683501_1.QUB[13.157,27.100]/0

    if(clickType == 'shiftClick'){
        this.shiftClickUpdate(y_click);
        var urlVars = this.getUrlVars();
        console.log('CONTINUUM IS',typeof urlVars['continuum'],urlVars['continuum'])
        /*
        updated method to get_spectrum_data
        if(typeof urlVars['continuum'] != "undefined"){
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+x_click+'&continuum='+urlVars['continuum'];
            var url = this.hsibase+'search/'+resource_name+'/'+resource_name+x_click+'/'+urlVars['continuum'];
        }
        else 
            {
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+x_click;
            var url = this.hsibase+'search/'+resource_name+'/'+resource_name+x_click+'/null';
        }*/
        if(typeof urlVars['continuum'] != "undefined"){
            urlVars['continuum'] = urlVars['continuum'].replace('/','');
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+x_click+'&continuum='+urlVars['continuum'];
            var url = this.hsibase+'get_spectrum_data/'+resource_name+x_click+'/0/'+urlVars['continuum'];
        }
        else 
            {
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+x_click;
            var url = this.hsibase+'get_spectrum_data/'+resource_name+x_click+'/0/0';
        }
        
        $('#share a').attr('href',sharable_url);
        var pushObj = typeof urlVars['continuum'] == "undefined" ? {cube:resource_name,spectra:resource_name+x_click} : {cube:resource_name,spectra:resource_name+x_click,continuum:urlVars['continuum']};
        pushObj.clickType = "shiftClick";
        if(y_click != 'popstate') history.pushState(pushObj,'hsifind',sharable_url);
        this.clearMarkers();
        var that = this;
        var a = x_click.replace('[','').replace(']','').split(',');
        $.each(a,function(i,x){
            var f = x.split('.');
            var projXy = that.projectXyToLatLon(f[1],f[0]);
            that.addNewMarker(projXy.x,projXy.y);
            console.log('getting spectrum data',projXy,f)
        })
        
    }
    else if(clickType == 'left'){
        this.removeShiftClickButton();
        this.showLoading();
        this.clearMarkers();
        var that = this;
        var projXy = that.projectXyToLatLon(x_click,y_click);
        that.addNewMarker(projXy.x,projXy.y);
        //console.log('pxy',projXy)
        /*var ltln = new OpenLayers.LonLat(projXy.x,projXy.y);//this.map.getLonLatFromPixel(projXy.x,projXy.y);
        var marker = new OpenLayers.Marker(ltln,that.icon.clone());
        marker.markerIndex = that.allMarkers.length;
        that.allMarkers.push(marker);
        that.markers.addMarker(marker);*/
        var urlVars = that.getUrlVars();
        console.log('urlvars',urlVars)
        if(typeof urlVars['continuum'] != "undefined"){
            urlVars['continuum'] = urlVars['continuum'].replace('/','');
            var url = this.hsibase+'search/'+resource_name+'/'+resource_name+'.'+y_click+'.'+x_click+'/'+urlVars['continuum'];
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+'['+y_click+'.'+x_click+']&continuum='+urlVars['continuum'];
            history.pushState({cube:resource_name,spectra:resource_name+'.'+y_click+'.'+x_click,continuum:urlVars['continuum']},'hsifind',sharable_url);
        }
        else{
            var url = this.hsibase+'search/'+resource_name+'/'+resource_name+'.'+y_click+'.'+x_click+'/0';
            var sharable_url = '?cube='+resource_name+'&spectra='+resource_name+'['+y_click+'.'+x_click+']';
            history.pushState({cube:resource_name,spectra:resource_name+'.'+y_click+'.'+x_click},'hsifind',sharable_url);
        }
        $('#share a').attr('href',sharable_url);
        
    }
    //makes the calls
    $('#share').fadeIn();
    var that = this;
    if(typeof that.cachedResults[url] == "undefined"){
        console.log("UNDEFINED",that.cachedResults,that.cachedResults[url],url)
        $.ajax({
            url:url,
            type:'get',
            dataType:'jsonp',
            success:function(d){
                handleResult(d)
            }
        });
    }
    else{
        handleResult(that.cachedResults[url]);
    }
    //inline method
    function handleResult(d){
        that.cachedResults[url] = d;
        console.log("GOT DATA",d)
            if(d.result){
                if(clickType == 'left'){
                    $.each(that.hsi_active,function(i,x){
                        that.map.removeLayer(x);
                    });
                    that.hsi_active = [];
                }
                that.hideLoading();
                var out_map = that.hsi_service_base+d.result.files[0];
                //that.addMapLayer(out_map,'map overlay');
                //REMOVED ABOVE addMapLayer
                var superpixel = that.hsi_service_base+d.result.files[1];
                if(clickType == 'left')
                    that.addMapLayer(superpixel,'superpixel');
                //that.map.setLayerIndex(superpixel,1)
                that.markers.setZIndex(50000);
                var spectrum = that.hsi_service_base+d.result.files[2];
                var multiband_indicator = resource_name.indexOf('MULTIBAND') >= 0 ? 'multiband' : 'nonmultiband';
                //that.addMapLayer(spectrum,'spectrum');
                var dataHsiRef = clickType == 'shiftClick' ? resource_name+x_click : resource_name+'.'+y_click+'.'+x_click
                
                //DEPRECATED WITH THE NEW NVD3 LIBRARY:: 
                //$('#spec_img').html('<div id="save_icon"></div><img class="draggable_image '+multiband_indicator+'" data-hsi-ref="'+dataHsiRef+'" src="'+that.hsi_service_base+d.result.files[3]+'" />');
                $('#spec_img svg').attr('data-imgurl',that.hsi_service_base+d.result.files[3])
                $('#spec_img svg').attr('data-hsiref',dataHsiRef);
                $('#spec_img svg').addClass('draggable_image');
                var lbl = clickType == 'shiftClick' ? 'Accrual: '+x_click : 'Original: '+x_click ;
                var obj = {label:lbl,data:d.result.stdout};
                if(d.result.stdout.length > 1000){
                    
                    if(clickType == 'left'){
                        that.makeChart([obj]);
                        that.spectraBase = obj;
                    }
                    else{
                        if(typeof that.spectraBase == "undefined"){
                            that.spectraBase = obj;
                            that.makeChart([obj]); 
                        }
                        else{
                            that.makeChart([that.spectraBase,obj]);  
                        }
                    }
                    
                }
                $('#spectrum h3').html('Spectrum for '+that.map.baseLayer.name+' <a href="#">Hide</a>');
                $('#spectrum').addClass('spec_showing');
                that.initjQueryUI();
                
            }
    }
}
hsiFind.prototype.retrieveSpectralLib = function(){
    var that = this;
    var lc = new Lawnchair(function(){
        this.where('record.type === "spectrum"',function(records){
            $('#spec_lib').html('<table width="580" id="spectral_library_table"></table>');
            $('#spec_lib table').append('<thead><tr><th>thumbnail</th><th>name</th><th>spectrum_id</th><th>original_target</th><th>generated</th></tr></thead>');
            $('#spec_lib table').append('<tbody />');
            $.each(records,function(ind,rec){
                var link = '?cube='+rec.original_target+'&spectra='+rec.spectrum_id;
                var multiband_indicator = rec.spectrum_id.indexOf('MULTIBAND') >= 0 ? 'multiband' : 'nonmultiband';
                var row = $('<tr rel="'+rec.original_target+'" data-hsi-ref="'+rec.spectrum_id+'" class="draggable_spectra '+multiband_indicator+'" />');
                $(row).append('<td><img class="table_thumb" src="'+rec.full_img+'" /></td>');
                $(row).append('<td><a data-spectra-id="'+rec.spectrum_id+'" data-cube-id="'+rec.original_target+'" class="name_link" href="'+link+'">'+rec.name+'</a></td>');
                $(row).append('<td>'+rec.spectrum_id+'</td>');
                $(row).append('<td>'+rec.original_target+'</td>');
                $(row).append('<td>'+rec.time+'</td>');
                $('#spec_lib table tbody').append(row);
            });
            $('#spec_lib tr').draggable({
                revert: 'invalid',
                cursor: 'move',
                helper: "clone",
                refreshPositions:true,
                appendTo:'body',
                start:function(){
                    that.showSlides();
                    that.isDragging = true;
                    if($(this).hasClass('multiband')){
                        that.highlightMultiband('multiband');
                    }
                    else{
                        //non multiband
                        that.highlightMultiband('nonmultiband');
                    }
                },
                stop: function(){
                    that.isDragging = false;
                    that.highlightMultiband('off');
                }
            });
            
            that.initjQueryUI();

            $('#spec_lib table').tablesorter();

        });
    });
}
hsiFind.prototype.highlightMultiband = function(target){
    
    switch(target){
        case 'multiband':
            $('.nonmultiband_target').css('opacity','0.1').removeClass('highlighted_target');
            $('.multiband_target').css('opacity','1.0').addClass('highlighted_target');
        break;
        case 'nonmultiband':
            $('.nonmultiband_target').css('opacity','1.0').addClass('highlighted_target');
            $('.multiband_target').css('opacity','0.1').removeClass('highlighted_target');
        break;
        case 'off':
            $('.nonmultiband_target').css('opacity','1.0').removeClass('highlighted_target');
            $('.multiband_target').css('opacity','1.0').removeClass('highlighted_target');
        break;

    }
}
hsiFind.prototype.updatejQueryUI = function(){
    $('#slidetray img, #map').droppable('destroy');
    this.initjQueryUI();
}
hsiFind.prototype.initjQueryUI = function(){
    var that = this;
    $('#spec_img img').draggable({
        revert: 'invalid',
        cursor: 'move',
        helper: "clone",
        cursorAt:{
            left:50,
            top:50
        },
        refreshPositions:true,
        appendTo:'body',
        start:function(){
            $(this).addClass('spec_showing');
            if($(this).hasClass('multiband')){
                that.highlightMultiband('multiband');
            }
            else{
                //non multiband
                that.highlightMultiband('nonmultiband');
            }
            that.showSlides();
            that.isDragging = true;
        },
        stop: function(){
            that.highlightMultiband('off');
            $(this).removeClass('spec_showing')
            that.isDragging = false;
        }
    })
    $('#slidetray img.multiband_target').droppable({
        accept:'.draggable_spectra.multiband, .draggable_image.multiband',
        hoverClass:'image_hovered',
        tolerance:'pointer',
        drop:function(event,ui){
            var base_map = $(this).attr('rel');
            that.is_popstate = true;
            $(this).trigger('click');
            var spectra_id = $(ui.draggable).attr('data-hsi-ref');
            that.retrieveLibraryResult(spectra_id,base_map);

        }
    });
    $('#slidetray img.nonmultiband_target').droppable({
        accept:'.draggable_spectra.nonmultiband, .draggable_image.nonmultiband',
        hoverClass:'image_hovered',
        tolerance:'pointer',
        drop:function(event,ui){
            var base_map = $(this).attr('rel');
            that.is_popstate = true;
            $(this).trigger('click');
            var spectra_id = $(ui.draggable).attr('data-hsi-ref');
            that.retrieveLibraryResult(spectra_id,base_map);

        }
    });
    $('#map').droppable({
        accept:'.draggable_spectra',
        tolerance:'pointer',
        drop:function(event,ui){
            that.hideLibrary();
            var spectra_id = $(ui.draggable).children('td').eq(2).html()
            var base_map = that.map.baseLayer.name;
            that.retrieveLibraryResult(spectra_id,base_map);

        }
    });
}
hsiFind.prototype.getAllBaseLayers = function(){
    //builds our thumbnail navigation of the baselayers
    var layers = this.results;
    var ret = '';
    var r_wid = 0;
    var that = this;
    $.each(layers,function(key,x){
        var url = that.hsi_service_base+x.result.files[4];
        var small_url = url.replace('browse','thumb');
        var multi_indicator = key.indexOf('MULTIBAND') >= 0 ? 'multiband_target' : 'nonmultiband_target';
        ret += '<img class="'+multi_indicator+'" src="'+small_url+'" data-full="'+url+'" rel="'+key+'" />'; 
    });

    $('#thumbs #slidetray').html(ret);
    //show all scenes when we're hovering over the slides on bottom
    $('#slides').hover(
        function(){

            that.showSlides();
        },function(){
            that.hideSlides();
    });
    
    //and some hooks for image thumb clicks
    $(document).on('click','#thumbs #slidetray img',function(e){
        that.clearMarkers();
        that.showLoading();
        var urlVars = that.getUrlVars();

        var pushUrl = typeof urlVars['continuum'] == "undefined" ? 'index.html?cube='+$(this).attr('rel') : 'index.html?cube='+$(this).attr('rel')+'&continuum='+urlVars['continuum'];
        var pushObj = typeof urlVars['continuum'] == "undefined" ? {cube:$(this).attr('rel')} : {cube:$(this).attr('rel'),continuum:urlVars['continuum']};
        if(!that.is_popstate) history.pushState(pushObj,'hsifind',pushUrl)
        else{ that.is_popstate = false;}
        $('#thumbs #slidetray img').removeClass('active_thumb');
        $(this).addClass('active_thumb');
        var r = $(this).attr('rel');
        var fullurl = $(this).attr('data-full');
        that.clickWidth = that.results[r].origWidth;
        that.clickHeight = that.results[r].origHeight;
        that.setBaseMap(fullurl,r);
        $.each(that.hsi_active,function(i,x){
            that.map.removeLayer(x);
        });
        that.hsi_active = [];

    });
    

}
hsiFind.prototype.showSlides = function(){
    var sth = $('#slidetray').height();
    $('#slides').css({'height':sth+'px','width':'1285px'});
}
hsiFind.prototype.hideSlides = function(){
    if(!this.isDragging) $('#slides').css({'height':'100px','width':'644px'});
}
hsiFind.prototype.showLoading = function(){
    $('#greybox').show();
    $('#loading').fadeIn();
}
hsiFind.prototype.hideLoading = function(){
    $('#greybox').fadeOut();
    $('#loading').fadeOut();
}
//ok so to get some d3 charting
hsiFind.prototype.makeChart = function(data){
    var that = this;
    //d3.select('')
    nv.addGraph(function() {
      that.chart = nv.models.lineChart()
      .options({
        margin: {left: 80, bottom: 50},
        x: function(d) { return d.x},
        y: function(d){ return d.y},
        showXAxis: true,
        showYAxis: true,
        transitionDuration: 250
      })
      .width($('#specSvg').width()-40)
      .height($('#specSvg').height())
      

      // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the parent chart, so need to chain separately
      that.chart.xAxis
        .axisLabel("Wavelength")
        .tickFormat(d3.format(',.1f'));

      that.chart.yAxis
        .axisLabel('Magnitude')
        .tickFormat(d3.format(',.1f'));

      d3.select('#spec_img svg')
        .datum(that.makeChartData(data))
        .call(that.chart);

      //TODO: Figure out a good way to do this automatically
      //nv.utils.windowResize(that.chart.update);
      //nv.utils.windowResize(function() { d3.select('#chart1 svg').call(chart) });

      //that.chart.dispatch.on('stateChange', function(e) { nv.log('New State:', JSON.stringify(e)); });

      return that.chart;
    });
}
hsiFind.prototype.updateChart = function(data){
    var d = this.makeChartData(data);
    d3.select('#spec_img svg')
        .datum(d)
        .call(that.chart);
}
hsiFind.prototype.makeChartData = function(data){
    var that = this
    var all = [];
    var cscale = d3.scale.category10();
    var minX, maxX;
    $.each(data,function(di,dataobj){
        console.log('splitting',dataobj)
        var d = dataobj.data.split(' ');
        var num = parseInt(d[0]);
        d.splice(0,1);
        console.log('d is stuff',d)
        var ret = []
        for(i=0;i<num;i++){
            if(typeof minX == "undefined") minX = d[i];
            if(typeof maxX == "undefined") maxX = d[i];
            minX = d[i] < minX ? d[i] : minX;
            maxX = d[i] > maxX ? d[i] : maxX;
            ret.push({x:parseFloat(d[i]),y:parseFloat(d[i+num])})
        }

        console.log('rets',ret)
        all.push({
            key:dataobj.label,
            color:cscale(di),
            values:ret
        });
    })
    setTimeout(function(){
        that.continuumScale = d3.scale.linear().domain([0,$('#specSvg .nv-wrap rect').eq(0).attr('width')]).range([minX,maxX]);
        that.reverseContinuumScale = d3.scale.linear().range([0,$('#specSvg .nv-wrap rect').eq(0).attr('width')]).domain([minX,maxX]);
        
    },100)
    return all;
}

//begin auxillary riffraff
function getCoordinates(e) {
 //console.log(e.xy);
}
//range convert
function convertToRange(value, srcRange, dstRange){
  // value is outside source range return
  if (value < srcRange[0] || value > srcRange[1]){
    return NaN; 
  }
  var srcMax = srcRange[1] - srcRange[0],
      dstMax = dstRange[1] - dstRange[0],
      adjValue = value - srcRange[0];
  return (adjValue * dstMax / srcMax) + dstRange[0];
}