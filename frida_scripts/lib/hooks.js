function url_init(){

    var url = Java.use("java.net.URL");

    url.$init.overload('java.lang.String').implementation = function (var0) {
        if(! var0.startsWith("null")){
            send("URL(" + var0 +")" );
        }
        return this.$init(var0);
    };

}

function to_string(){
    const String = Java.use('java.lang.String');

    String.toString.implementation = function(){
        const x  = this.toString()
        if(x.length > 5){
            send("to_string("+x+")")
        }
        return x
    }
}

function dexclass_loader(){
    var DexClassLoader = Java.use("dalvik.system.DexClassLoader");

    DexClassLoader.$init.implementation = function(dexPath,optimizedDirectory,librarySearchPath,parent){
            send("dexclassloader(" + dexPath + "," + optimizedDirectory + "," + librarySearchPath + "," + parent + ")")
            this.$init(dexPath,optimizedDirectory,librarySearchPath,parent);
    }
}

exports.to_string = to_string
exports.dexclass_loader = dexclass_loader
exports.url_init = url_init