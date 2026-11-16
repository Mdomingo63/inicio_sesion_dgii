# Inspección del campo Tarjeta — DGII

## Resultado confirmado

Página: https://www.dgii.gov.do/OFV/login.aspx

El campo Tarjeta está presente en la etapa posterior a Usuario y Clave. Se hizo hover y se observó el tooltip visible. No se introdujo ningún código de tarjeta ni se pulsó Continuar.

Texto exacto observado:

> Favor introducir el código número: 19 de su tarjeta

La posición solicitada en esta sesión es **19**; no debe fijarse como constante para otras sesiones.

## Ubicación del mensaje

`title` devuelve una cadena vacía (`""`). El texto está en el atributo `data-original-title` del input y en un elemento flotante con clase `.tooltip-inner`. No se observó un atributo `data-*` separado que contenga exclusivamente el número.

El input tiene `data-toggle="tooltip"` y `data-placement="right"`. Durante la observación, `aria-describedby="tooltip455569"` enlaza con el contenedor flotante `#tooltip455569`. Conviene resolver esa relación en cada ejecución, sin fijar el ID observado.

Selector del campo: `#ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken`.

Selector del mensaje visible en esta observación: `#tooltip455569 .tooltip-inner`.

## HTML exacto del input

```html
<input name="ctl00$ContentPlaceHolder1$txtpasscodeTarjetaToken" type="password" id="ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken" class="form-control input-sm token" data-toggle="tooltip" data-placement="right" title="" style="width:150px;" data-original-title="Favor introducir el código número: 19 de su tarjeta" aria-describedby="tooltip455569">
```

## Todos los atributos

```json
[
  {
    "name": "name",
    "value": "ctl00$ContentPlaceHolder1$txtpasscodeTarjetaToken"
  },
  {
    "name": "type",
    "value": "password"
  },
  {
    "name": "id",
    "value": "ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken"
  },
  {
    "name": "class",
    "value": "form-control input-sm token"
  },
  {
    "name": "data-toggle",
    "value": "tooltip"
  },
  {
    "name": "data-placement",
    "value": "right"
  },
  {
    "name": "title",
    "value": ""
  },
  {
    "name": "style",
    "value": "width:150px;"
  },
  {
    "name": "data-original-title",
    "value": "Favor introducir el código número: 19 de su tarjeta"
  },
  {
    "name": "aria-describedby",
    "value": "tooltip455569"
  }
]
```

## Elementos flotantes encontrados

La consulta solicitada devolvió el contenedor, su flecha y su texto:

```html
<div class="tooltip fade right in" role="tooltip" id="tooltip455569" style="top: 304.953px; left: 1190.05px; display: block;"><div class="tooltip-arrow" style="top: 50%;"></div><div class="tooltip-inner">Favor introducir el código número: 19 de su tarjeta</div></div>
<div class="tooltip-arrow" style="top: 50%;"></div>
<div class="tooltip-inner">Favor introducir el código número: 19 de su tarjeta</div>
```

## Lectura del mensaje y la posición

Este código puede ejecutarse cuando el campo ya exista. Lee primero el atributo, sin depender de que el tooltip esté visible:

```javascript
const campo = document.getElementById('ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken');
const tooltipId = campo?.getAttribute('aria-describedby');
const mensaje = campo?.getAttribute('data-original-title')
  || campo?.title
  || (tooltipId && document.getElementById(tooltipId)?.querySelector('.tooltip-inner')?.textContent)
  || '';
const posicion = mensaje.match(/número:\s*(\d+)/i)?.[1] ?? null;
({ mensaje, posicion });
```

La lectura directa del DOM confirmó el mensaje citado. Este fragmento se ofrece como implementación basada en los atributos observados; no introduce ni envía el segundo factor.

## HTML completo del contenedor de acceso

La consulta original `document.querySelector('.form-acceso, #form1, [class*="acceso"]')` no encontró ningún elemento. El formulario exterior real es `#aspnetForm`; el contenedor específico de acceso es `#ctl00_ContentPlaceHolder1_formularioLogin`, que contiene la tabla `#Table2`.

A continuación se reproduce el contenedor completo, omitiendo valores de credenciales y campos ocultos, si los hubiera. No se exportan estados internos del formulario exterior.

```html
<div id="ctl00_ContentPlaceHolder1_formularioLogin" onkeypress="javascript:return WebForm_FireDefaultButton(event, 'ctl00_ContentPlaceHolder1_BtnAceptar')" style="float: left;">
	
                                        <table id="Table2" style="margin-left: 5px; width: 97%">
                                            <tbody><tr>
                                                <td class="style2" colspan="3" align="center">&nbsp;</td>
                                            </tr>
                                            <tr>
                                                <td rowspan="3" align="right" class="style5">
                                                    <div class="candado">
                                                        <img src="/OFV/Estilos/imagenes/spacer.gif" height="34" width="36" alt="">
                                                    </div>
                                                </td>
                                                <td class="style3" align="right">
                                                    <span id="ctl00_ContentPlaceHolder1_reqUsuario" class="errorMsg" style="color:Red;display:none;">*</span>
                                                    Usuario&nbsp;
                                                </td>
                                                <td style="text-align: right">
                                                    <input name="ctl00$ContentPlaceHolder1$txtUsuario" type="text" value="[OMITIDO]" maxlength="20" id="ctl00_ContentPlaceHolder1_txtUsuario" disabled="disabled" class="form-control input-sm" style="width:150px;">
                                                </td>
                                            </tr>
                                            <tr>
                                                <td class="style3" align="right">
                                                    <span id="ctl00_ContentPlaceHolder1_reqPassword" class="errorMsg" style="color:Red;display:none;">*</span>
                                                    <span id="ctl00_ContentPlaceHolder1_lblclave">Clave</span>&nbsp;
                                                </td>
                                                <td style="text-align: right">
                                                    <input name="ctl00$ContentPlaceHolder1$txtPassword" type="password" id="ctl00_ContentPlaceHolder1_txtPassword" disabled="disabled" class="form-control input-sm" style="width:150px;background:#f0f0f0 url('/ofv/imagenes/mascarilla.gif') no-repeat 5px center;">
                                                </td>
                                            </tr>
                                            <tr>
                                                <td align="right">
                                                    <span id="ctl00_ContentPlaceHolder1_lblinfoTarjetaToken">Tarjeta</span>&nbsp;
                                                </td>
                                                <td style="text-align: right">
                                                    <input name="ctl00$ContentPlaceHolder1$txtpasscodeTarjetaToken" type="password" id="ctl00_ContentPlaceHolder1_txtpasscodeTarjetaToken" class="form-control input-sm token" data-toggle="tooltip" data-placement="right" title="" style="width:150px;" data-original-title="Favor introducir el código número: 19 de su tarjeta" aria-describedby="tooltip455569"><div class="tooltip fade right in" role="tooltip" id="tooltip455569" style="top: 304.953px; left: 1190.05px; display: block;"><div class="tooltip-arrow" style="top: 50%;"></div><div class="tooltip-inner">Favor introducir el código número: 19 de su tarjeta</div></div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td colspan="3" style="height: 5px" align="center">
                                                    <span id="ctl00_ContentPlaceHolder1_lblMensaje" class="errorMsg"></span>
                                                    <span id="ctl00_ContentPlaceHolder1_lblinfoCodigo" style="color:Red;font-size:8pt;"></span>
                                                    
                                                </td>
                                            </tr>
                                            <tr>
                                                <td colspan="3" align="right">

                                                    <div class="limpiar">
                                                    </div>
                                                    <div style="width: 100%; margin-bottom: 10px; border: none;">
                                                        <div id="ctl00_ContentPlaceHolder1_UpdatePanel1">
		
                                                                <span id="rsc" style="display: none"></span>
                                                                
                                                            
	</div>
                                                    </div>
                                                    <div style="float: right;">
                                                        <input type="submit" name="ctl00$ContentPlaceHolder1$BtnAceptarTarjetaToken" value="Continuar" id="ctl00_ContentPlaceHolder1_BtnAceptarTarjetaToken" class="form-control btn-success">
                                                        
                                                    </div>
                                                </td>
                                            </tr>
                                        </tbody></table>
                                    
</div>
```

## Evidencia del hover

Captura con el cursor sobre Tarjeta y el mensaje visible:

![Campo Tarjeta y tooltip visible](/home/ubuntu/screenshots/screenshot_1794863402878.png)
