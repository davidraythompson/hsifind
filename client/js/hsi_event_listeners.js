hsiFind.prototype.initClickListeners = function(){
    var that = this;
    $(document).on('click','#spectrum h3 a',function(){
        $('#spectrum').removeClass('spec_showing').addClass('spec_half_showing');
    });
    $(document).on('click','.spec_half_showing #right_spec',function(){
        $('#spectrum').addClass('spec_showing').removeClass('spec_half_showing');
    });
    $(document).on('click','#show_library_button',function(e){
        console.log('click');
        if(!$(this).hasClass('showing')){
            that.showLibrary();
            
            $(this).addClass('showing');
        }
        else {
            that.hideLibrary();
            $(this).removeClass('showing')
        }

    });
    $(document).on('click','.right_spec a',function(e){
        e.preventDefault();
        that.hideLibrary();
    });
    //save spectrum button clicks
    $(document).on('click','#save_icon',function(e){
        
        /*var lc = new Lawnchair(function(){
            this.save({type:'spectrum',spectrum_id:img_id,original_target:target_id,name:'foo',time:Math.floor(new Date().getTime()/1000),thumb_img:imghref.replace('spectrum','thumb'),full_img: imghref},function(r){
                console.log('saved',r);
            });
        });*/
        that.showGreybox();
        $('#choose_a_name').fadeIn();

    });
    //cancel our spectra accrual
    $(document).on('click','#cancelbutton',function(e){
        var dv = -1 * parseInt($(this).attr('data-count'));
        history.go(dv);
        that.removeShiftClickButton();
    })
    //make sure to set window for continuum
    var urlVars = that.getUrlVars();
    //check if there is a continuum
    if(typeof urlVars['continuum'] != "undefined"){
        var sI = setInterval(function(){
            if($('#specContinuum').length > 0 && typeof that.reverseContinuumScale != "undefined"){
                
                var parts = urlVars['continuum'].split(',')
                var l1 =  that.reverseContinuumScale(parts[0])+100
                var l2 = that.reverseContinuumScale(parts[1])+100
                var w = l2-l1;
                $('#specContinuum').css('height',$('#specSvg .nv-wrap rect').eq(0).attr('height'))
                $('#specContinuum').css('top','28px')
                $('#specContinuum').css('left',l1);
                $('#specContinuum').css('width',w);
                clearTimeout(sI);
            }
        },10);
        
        
    }
    //save our spectra accrual
    $(document).on('click','#gobutton',function(e){
        var urlp = that.getUrlVars();
        var cube = urlp['cube'];
        var sp = urlp['spectra'];
        that.retrieveLibraryResult(sp,cube);
    })
    $(document).on('click','.submit_button',function(e){
        //name is submitted for saving
        /*var img_id = $.trim($('#spec_img img').attr('data-hsi-ref'));
        var imghref = $('#spec_img img').attr('src');*/
        //removed img in favor of svg
        var img_id = $.trim($('#spec_img svg').attr('data-hsi-ref'));
        var imghref = $('#spec_img svg').attr('data-imgurl');
        var target_id = that.map.baseLayer.name;//img_id.split('.')[0];
        that.saveSpectra(img_id,imghref,target_id);
    });
    $(document).on('click','.cancel_button',function(e){
        $('#choose_a_name').fadeOut();
        that.hideGreybox();
    });
    $(document).on('click','.name_link',function(e){
        e.preventDefault();
        var spectraid = $(this).attr('data-spectra-id');
        var cubeid = $(this).attr('data-cube-id');
        $('#slidetray img[rel="'+cubeid+'"]').trigger('click');
        that.clearMarkers();
        that.retrieveLibraryResult(spectraid,cubeid);
    });
    //opacity slider
    $(document).on('change','#opacityRange input[type="range"]',function(e){
        var v = $(this).val();
        $.each(that.hsi_active,function(i,x){
            if(typeof x.setOpacity != "undefined"){
                x.setOpacity(v);
            }
        })
    });

    
    //ok continuum drag & drop...
    $(document).on('mousedown',$('#specSvg .nv-wrap rect').eq(0),function(e){
        console.log('mouseodnw')
        that.svgMouseDown = true;
        console.log('down ',e)

        that.svgMouseStartX = e.offsetX+20;//e.pageX - $('#specSvg .nv-wrap rect').eq(0).offset().left;
    });
    $(document).on('mousemove',$('#specSvg .nv-wrap rect').eq(0),function(e){
        console.log('mousemove',that.svgMouseDown)
        if(!that.svgMouseDown) return;
        else{
            var mx = e.offsetX+20;;
            that.svgMouseEndX = mx;
            var w = Math.abs(mx - that.svgMouseStartX);
            var start = that.svgMouseStartX;//mx < that.svgMouseStartX ? mx : that.svgMouseStartX;
            $('#specContinuum').css('left',start);
            $('#specContinuum').css('width',w)
            $('#specContinuum').css('height',$('#specSvg .nv-wrap rect').eq(0).attr('height'))
            $('#specContinuum').css('top','28px')
        }
    })
    $(document).on('mouseup',$('#specSvg .nv-wrap rect').eq(0),function(){
        that.svgMouseDown = false;
        var bscale = Math.round(that.continuumScale(that.svgMouseStartX-100)*100)/100;
        var escale = Math.round(that.continuumScale(that.svgMouseEndX-100)*100)/100;
        var urlVars = that.getUrlVars();
        if(!isNaN(bscale) && !isNaN(escale)){
            console.log('urlvars',urlVars,urlVars['continuum'])
            //var sharable_url = typeof urlVars['continuum'] == "undefined" ? '?cube='+urlVar+'&spectra='+spectra_id : '?cube='+base_id+'&spectra='+spectra_id+'&continuum='+urlVars['continuum'];
            var sharable_url = '?';
            $.each(urlVars,function(i,x){
                sharable_url += '&'+i+'='+x;
            });
            var contstr = bscale+','+escale+',0.05';
            
            if(typeof urlVars['continuum'] == "undefined"){
                urlVars['continuum'] = contstr;
                sharable_url += '&continuum='+contstr;
            }
            //if(spectra_id.indexOf(base_id) == -1) this.clearMarkers();
            //this.clearMarkers();
            $('#share a').attr('href',sharable_url);
            //var pushObj = typeof urlVars['continuum'] == "undefined" ? {cube:url,spectra:spectra_id} : {cube:base_id,spectra:spectra_id,continuum:urlVars['continuum']};
            history.pushState(urlVars,'hsifind',sharable_url);
            //console.log('bend',bscale,that.svgMouseStartX,escale,that.svgMouseEndX)
        }
    });
    window.onpopstate = function(event){
        event.preventDefault();
        var loc = document.location;
        var state = event.state;
        console.log('state is ',event);
        if(state != null){
            if(typeof state.cube != "undefined" && typeof state.spectra != "undefined"){
                that.is_popstate = true;
                if(typeof state.clickType != "undefined"){
                    var pointStr = '['+state.spectra.split('[')[1];
                    that.retrieveClick('shiftClick',state.cube,pointStr,'popstate');
                }
                else{
                    $('#slidetray img[rel="'+state.cube+'"]').trigger('click');
                    that.retrieveLibraryResult(state.spectra,state.cube,true);
                }
            }
            else if(typeof state.cube != "undefined" && typeof state.spectra == "undefined"){
                that.is_popstate = true;
                $('#slidetray img[rel="'+state.cube+'"]').trigger('click');
                that.clearMarkers();
            }
            else {
                //do nothing?
            }

        }
    }
}
hsiFind.prototype.saveSpectra = function(spectra_id,img_href,target_id){
    var that = this;
    var lc = new Lawnchair(function(){
            this.save({type:'spectrum',spectrum_id:spectra_id,original_target:target_id,name:$('#choose_a_name input').val(),time:Math.floor(new Date().getTime()/1000),thumb_img:img_href.replace('spectrum','thumb'),full_img: img_href},function(r){
                $('#choose_a_name').fadeOut();
                that.hideGreybox();
                that.showLibrary();
                $('#choose_a_name input').val('');
            });
        });
}
hsiFind.prototype.showGreybox = function(){
    $('#greybox').fadeIn();
}
hsiFind.prototype.hideGreybox = function(){
    $('#greybox').fadeOut();

}