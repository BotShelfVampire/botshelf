// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

import java.lang.annotation.*;
@Documented @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD)
public @interface Configurable { String value(); String description() default ""; }
