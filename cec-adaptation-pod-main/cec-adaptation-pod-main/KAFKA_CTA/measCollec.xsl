<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:mcf="http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec">

<xsl:output method="text" encoding="utf-8"/>

<xsl:template match="/">
    <!-- <xsl:for-each select="/mcf:measCollecFile/mcf:measData/mcf:measInfo/mcf:measValue"> -->
    <xsl:for-each select="/mcf:measCollecFile/mcf:measData/mcf:measInfo">
        <xsl:variable name="measInfoId"><xsl:value-of select="@measInfoId"/></xsl:variable>
        <xsl:for-each select="mcf:measValue/mcf:r">
            <!--<xsl:variable name="pos"><xsl:value-of select="position()"/></xsl:variable> -->
            <xsl:variable name="pos"><xsl:value-of select="@p"/></xsl:variable>

            <xsl:text>measInfoId=</xsl:text>
            <xsl:value-of select="$measInfoId"/>
            <xsl:text>,</xsl:text>

            <xsl:value-of select="/mcf:measCollecFile/mcf:fileHeader/@dnPrefix"/>
            <xsl:text></xsl:text>
            <xsl:value-of select="../../../mcf:managedElement/@localDn"/>
            <xsl:text>,</xsl:text>
            <xsl:value-of select="../@measObjLdn"/>
            <xsl:text>,tl_timestamp=</xsl:text>
            <xsl:value-of select="../../mcf:granPeriod/@endTime"/>
            <xsl:text>,countername=</xsl:text>

            <!-- <xsl:value-of select="../../mcf:measType[position()=$pos]"/>-->
            <xsl:for-each select="../../mcf:measType">
               <xsl:if test="@p=$pos">
                  <xsl:value-of select="."/>
               </xsl:if>
            </xsl:for-each>

            <xsl:text>,countervalue=</xsl:text>
            <xsl:value-of select="."/>
            <xsl:text>&#10;</xsl:text>
        </xsl:for-each>
    </xsl:for-each>
</xsl:template>

</xsl:stylesheet>

