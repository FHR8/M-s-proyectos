function validarFormulario() {
    if((nombre.value.length==0) || (apellidos.value.length==0) ||  (telefono.value.length==0) || 
      (dni.value.length==0) || (cElectronico.value.length==0)){
        alert("Alguno de los campos no están rellenos");
        return false;
    }
    if(nombre.value.length>50) {
        nombre.focus();
        alert("El nombre introducido es demasiado largo");
        return false;
    }
    if((apellidos.value.length<7) || (apellidos.value.length>70)) {
        apellidos.focus();
        alert("Los apellidos deben tener entre 7 y 70 caracteres");
        return false;
    }
    var telef=/^\d{3}\s\d{3}\s\d{3}$/
    if (!(telef.test(telefono.value))){
    alert("Lo siento, el telefono introducido no es correcto. Debe introducir un espacio cada 3 cifras");
    return false;
    }
    var identidad=/^[0-9]{8}[A-Z|a-z]{1}$/
    if(!(identidad.test(dni.value))){
        alert("El dni no es correcto");
        return false;
    }
    var emilio=/^\w+([\.-]?\w+)*@\w+([\.-]\w+)*(\.\w{2,4})+$/
    if(!((emilio.test)(cElectronico.value))){
        alert("El email no es correcto");
        return false;
    }
    alert("Los cambios han sido rellenados correctamente");
    return true;
}