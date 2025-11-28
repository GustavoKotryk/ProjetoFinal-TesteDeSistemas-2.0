*** Settings ***
Library    SeleniumLibrary
Library    Collections

*** Variables ***
${URL}    https://projetofinal-testedesistemas-2-0.onrender.com
${BROWSER}    chrome

*** Keywords ***
Abrir Navegador
    Open Browser    ${URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Implicit Wait    10 seconds

Fechar Navegador
    Close Browser

Deve Conter Mensagem
    [Arguments]    ${mensagem}
    Wait Until Page Contains    ${mensagem}    timeout=10s

Clicar E Esperar
    [Arguments]    ${locator}
    Wait Until Element Is Visible    ${locator}    timeout=10s
    Click Element    ${locator}

Preencher Campo
    [Arguments]    ${campo}    ${valor}
    Wait Until Element Is Visible    ${campo}    timeout=10s
    Input Text    ${campo}    ${valor}