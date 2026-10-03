package com.motivewave.platform.sdk.study;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
public @interface StudyHeader { String namespace(); String id(); String name(); String desc(); boolean overlay(); String menu() default ""; boolean signals() default false; }
