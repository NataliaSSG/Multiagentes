# Multiagentes  

Objetivo:  
El objetivo de este proyecto es identificar el impacto de un cruce peatonal inteligente, es decir, que permita el flujo de carros sin parar siempre y cuando no hayan peatones, esto con el fin de eliminar tiempos de espera innecesarios.

Para poder ejecutar la libreta de Jupyter (RetoFinal.ipynb), es necesario tener las librerías utilizadas descargadas. Para esto, se puede utilizar el siguiente comando en la terminal:  
  pip install agentpy numpy matplotlib ipython  

En la libreta, se muestra un sistema multiagente donde se simula una calle con un cruce peatonal. El cruce puede ser inteligente o normal dependiendo del parámetro dado. En la implementación inteligente, el semáforo se mantendrá en verde para permitir el flujo vehicular ininterrumpido. En el caso de que aparezca un peatón, tardará cierto tiempo para volverse rojo y permitir el paso del peatón. En la implementación normal, el semáforo cambia de color cada cierto tiempo, independientemente de la presencia de peatones. En la libreta también se muestran gráficas para demostrar la eficiencia del cruce inteligente.  

En la carpeta de Evidencia_1, se encuentra el proyecto donde se demuestra la conexión entre Python y Unity. En la carpeta de EvidenciaFinal, se encuentra una liga hacia el proyecto de Unity, el archivo python de cliente para la conexión, una liga hacia el video, y un README para saber cómo ejecutarlo.  
